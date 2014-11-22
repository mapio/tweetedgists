# Copyright (C) 2012 Massimo Santini <massimo.santini@unimi.it>
#
# This file is part of TweetedGists
#
# TweetedGists is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TweetedGists is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TweetedGists If not, see <http://www.gnu.org/licenses/>.

from json import loads
from os import environ as ENV

from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from flask_oauth import OAuth
from requests import get
from werkzeug.contrib.cache import MemcachedCache

# setup cache

if ENV[ 'VERSION' ] == 'devel':
	mc = None
else:
	from pylibmc import Client
	mc = Client(
		servers = [ ENV[ 'MEMCACHE_SERVERS' ] ],
		username = ENV[ 'MEMCACHE_USERNAME' ],
		password = ENV[ 'MEMCACHE_PASSWORD' ],
		binary = True
	)
cache = MemcachedCache( mc )

# setup oauth

oauth = OAuth()
twitter = oauth.remote_app( 'twitter',
	base_url = 'http://api.twitter.com/1/',
	request_token_url = 'http://api.twitter.com/oauth/request_token',
	access_token_url = 'http://api.twitter.com/oauth/access_token',
	authorize_url = 'http://api.twitter.com/oauth/authenticate',
	consumer_key = ENV[ 'TWITTER_CONSUMER_KEY' ],
	consumer_secret = ENV[ 'TWITTER_CONSUMER_SECRET' ]
)

# the app

__version__ = '0.0.1'

app = Flask(__name__)
app.secret_key = ENV[ 'SECRET_KEY' ]

# auth handling routes, inspired by https://github.com/mitsuhiko/flask-oauth

@app.before_request
def before_request():
	g.version = __version__
	g.user = None
	if 'user_id' in session:
		g.user = cache.get( session[ 'user_id' ] + '_username' )
		g.oauth_token = cache.get( session[ 'user_id' ] + '_oauth_token' )
		g.oauth_secret = cache.get( session[ 'user_id' ] + '_oauth_secret' )

@twitter.tokengetter
def get_twitter_token():
	if g.user is not None:
	    return g.oauth_token, g.oauth_secret

@app.route( '/login' )
def login():
	next_url = request.args.get( 'next' ) or request.referrer or url_for( 'index' )
	if 'user_id' in session and cache.get( session[ 'user_id' ] + '_username' ): return redirect( next )
	print url_for( 'oauth_authorized', next = next_url, _external = True )
	return twitter.authorize( callback = url_for(
		'oauth_authorized',
		next = next_url, _external = True
	) )

@app.route( '/oauth-authorized' )
@twitter.authorized_handler
def oauth_authorized( resp ):
	next_url = request.args.get( 'next' ) or url_for( 'index' )

	if resp is None:
		flash( u'You denied the request to sign in.' )
		return redirect( next_url )

	print resp.keys()
	session[ 'user_id' ] = resp[ 'user_id' ]
	cache.set( session[ 'user_id' ] + '_username', resp[ 'screen_name' ] )
	cache.set( session[ 'user_id' ] + '_oauth_token', resp[ 'oauth_token' ] )
	cache.set( session[ 'user_id' ] + '_oauth_secret', 	resp[ 'oauth_token_secret' ] )
	flash( u'You were signed in as <b>{0}</b>.'.format( resp[ 'screen_name' ] ) )

	return redirect( next_url )

@app.route( '/logout' )
def logout():
	session.pop( 'user_id', None )
	flash( u'You were signed out.' )
	return redirect( request.referrer or url_for( 'index' ) )

# the actual application

@app.route( '/' )
def index():
	if g.user: return redirect( url_for( 'list' ) )
	return render_template( 'index.html' )

def cached_get( key, *args, **kwargs ):
	result = cache.get( 'get_' + key )
	if result: return result
	result = get( *args, **kwargs )
	if result.status_code == 200:
		cache.add( 'get_' +  key, result.text )
		return result.text
	else:
		return None

@app.route( '/list' )
def list():
	if not g.user: return redirect( url_for( 'index' ) )

	res = []
	tweets = cached_get( 'tweets', 'http://search.twitter.com/search.json', params = { 'q': 'gist.github', 'rpp': '10', 'include_entities': 'true', 'show_user': 'true' } )
	tweets = loads( tweets )
	for t in tweets[ 'results' ]:
	    embed = cached_get( 'embed_{0}'.format( t[ 'id' ] ), 'https://api.twitter.com/1/statuses/oembed.json', params = { 'id': t['id'], 'align': 'center' } )
	    res.append( loads( embed )[ 'html' ].split( '\n' )[ 0 ] )
	    for u in t['entities']['urls']:
	        gg = u['expanded_url']
	        if 'gist.github.com' in gg:
	            res.append( '<script src="{0}.js"></script>'.format( gg ) )

	return render_template( 'list.html', content = '\n'.join( res ) )

if __name__ == '__main__':
	app.run( debug = True )
