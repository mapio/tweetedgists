from os import environ as ENV

from flask import Flask
from werkzeug.contrib.cache import MemcachedCache

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

app = Flask(__name__)

@app.route("/")
def hello():
	cache.get( "pippo" )
	return "Hello World!"

if __name__ == '__main__':
	app.run( debug = True )