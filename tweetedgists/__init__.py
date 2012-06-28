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

from os import environ as ENV

from flask import Flask, g, render_template, request, redirect, url_for, session, flash
from flaskext.oauth import OAuth
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
	user = g.user
	if user is not None:
	    return g.oauth_token, g.oauth_secret

@app.route( '/')
def index():
	return render_template( 'index.html' )

@app.route( '/login' )
def login():
	return twitter.authorize( callback = url_for( 
		'oauth_authorized', 
		next = request.args.get('next') or request.referrer or None 
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
	flash( u'You were signed in as <b>{0}</b>'.format( resp[ 'screen_name' ] ) )

	return redirect( next_url )

@app.route( '/logout' )
def logout():
	session.pop( 'user_id', None )
	flash( u'You were signed out.' )
	return redirect( request.referrer or url_for( 'index' ) )

if __name__ == '__main__':
	app.run( debug = True )
	
	
	
	
	
	
	
	
	
	
	
	
	
	





	# @app.route('/')
	# def index():
	#     tweets = None
	#     if g.user is not None:
	#         resp = twitter.get('statuses/home_timeline.json')
	#         if resp.status == 200:
	#             tweets = resp.data
	#         else:
	#             flash('Unable to load tweets from Twitter. Maybe out of '
	#                   'API calls or Twitter is overloaded.')
	#     return render_template('index.html', tweets=tweets)
	# 
	# 
	# @app.route('/tweet', methods=['POST'])
	# def tweet():
	#     """Calls the remote twitter API to create a new status update."""
	#     if g.user is None:
	#         return redirect(url_for('login', next=request.url))
	#     status = request.form['tweet']
	#     if not status:
	#         return redirect(url_for('index'))
	#     resp = twitter.post('statuses/update.json', data={
	#         'status':       status
	#     })
	#     if resp.status == 403:
	#         flash('Your tweet was too long.')
	#     elif resp.status == 401:
	#         flash('Authorization error with Twitter.')
	#     else:
	#         flash('Successfully tweeted your tweet (ID: #%s)' % resp.data['id'])
	#     return redirect(url_for('index'))
