"""
Copyright 2014 VoterChat

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import config, models

from flask import Flask, jsonify
app = Flask(__name__)
app.config.from_object("config")

import redis
r = redis.StrictRedis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB
)

### APP FUNCTIONS ###

@app.route("/user/<username>")
def get_user(username):
    """
    Given the username, return
    the profile of the user.
    """
    try:
        user = models.get_user(username)
        return jsonify(user.info())
    except Exception, e:
        return jsonify({
            "message": str(e)
        })

@app.route("/group/<groupname>")
def get_group(groupname):
    """
    Given the shortname of a group,
    return the profile of the group.
    """
    try:
        group = models.get_group(groupname)
        return jsonify(group.info())
    except Exception, e:
        return jsonify({
            "message": str(e)
        })

### APP FUNCTIONS ###

if __name__ == "__main__":
    app.run()
