#!/bin/bash

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

# trap TERM and change to QUIT
trap 'echo wrapper killing $PID; kill -QUIT $PID' TERM

# program to run
gunicorn tweetedgists:app -w 3 -b 0.0.0.0:$PORT &

# capture PID and wait
PID=$!
echo wrapper started $PID
wait
