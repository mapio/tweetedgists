from os import environ as ENV

from flask import Flask
from werkzeug.contrib.cache import MemcachedCache

import pylibmc

mc = pylibmc.Client(
	servers = [ ENV[ 'MEMCACHE_SERVERS' ] ],
	username = ENV[ 'MEMCACHE_USERNAME' ],
    password = ENV[ 'MEMCACHE_PASSWORD' ],
    binary = True
)

cache = MemcachedCache( [ mc ] )

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"
