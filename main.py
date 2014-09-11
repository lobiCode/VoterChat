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

# TODO: Require admin authentication.
@app.route("/api/flushdb")
def flushdb():
    """
    Flush the database.
    """
    r.flushdb()
    models.flushdb()

    app.logger.info("[DB] Database has been flushed.")
    return "", 200

@app.route("/api/user/<username>")
def get_user(username):
    """
    Return the profile of the user.
    """
    user = models.User(username)
    return jsonify(user.get()), 200

@app.route("/api/user/<username>/new", methods=["POST"])
def new_user(username):
    """
    Creates a new user.
    """
    if not request.form:
        abort(400)

    user = models.User(
        username,
        email=request.form.get("email", ""),
        phone_no=request.form.get("phone_no", "")
    )
    user.new()

    app.logger.info("[USER] User %s was created." % username)
    return jsonify(user.get()), 201

# TODO: Require either admin or user authentication.
@app.route("/api/user/<username>/delete")
def delete_user(username):
    """
    Delete a user.
    """
    user = models.User(username)
    user.delete()

    app.logger.info("[USER] User %s has been deleted." % username)
    return "", 200

# TODO: Require user authentication.
@app.route("/api/user/<recipient>/send", methods=["POST"])
def send_user(recipient):
    """
    Send a message to a user.
    """
    if not request.form:
        abort(400)
    if not "username" in request.form:
        return {
            "message": "Field 'username' was not specified."
        }, 400
    if not "content" in request.form:
        return {
            "message": "Field 'content' was not specified."
        }, 400

    sender = models.User(request.form["username"])
    recipient = models.User(recipient)

    msg = models.Message(
        models.new_id("message"),
        sender=sender.id,
        content=request.form["content"]
    )
    msg.new()
    msg.send_users([recipient.id])

    app.logger.info("[PM] %s -> %s" % (recipient.id, sender.id))
    return "", 200

# TODO: Require user authentication.
@app.route("/api/poll", methods=["POST"])
def poll():
    """
    Poll the server for new messages.
    """
    if not request.form:
        abort(400)
    if not "username" in request.form:
        return {
            "message": "Field 'username' was not specified."
        }, 400

    user = models.User(request.form["username"])
    msg_list = user.poll()

    app.logger.info(msg_list)
    return jsonify({"messages": msg_list}), 200

### APP FUNCTIONS ###

if __name__ == "__main__":
    app.run()
