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

### INITIALIZATION ###

import config

from flask import Flask, abort, jsonify, request
app = Flask(__name__)
app.config.from_object("config")

import redis
r = redis.StrictRedis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB
)

### INITIALIZATION ###


### APP FUNCTIONS ###

import models

@app.route("/api/flushdb")
def flushdb():
    """
    Flush the database.
    """
    r.flushdb()
    models.flushdb()

    app.logger.info("Database has been flushed.")
    return "", 200

@app.route("/api/user/<username>", methods=["GET"])
def get_user(username):
    """
    Return the profile of the user.
    """
    user = models.User(username)
    return jsonify(user.get()), 200

@app.route("/api/user/<username>", methods=["POST"])
def new_user(username):
    """
    Creates a new user.
    """
    app.logger.info(request.form)
    if not request.form:
        abort(400)
    user = models.User(
        username,
        email=request.form.get("email", ""),
        phone_no=request.form.get("phone_no", "")
    )
    user.new()
    return jsonify(user.get()), 201

@app.route("/api/group/<groupname>", methods=["GET"])
def get_group(groupname):
    """
    Returns the profile of the group.
    """
    group = models.Group(groupname)
    return jsonify(group.get())

@app.route("/api/group/<groupname>", methods=["POST"])
def new_group(groupname):
    """
    Creates a new group.
    """
    group = models.Group(
        groupname
    )
    group.new()
    return jsonify(group.get()), 201

### APP FUNCTIONS ###

if __name__ == "__main__":
    app.run()
