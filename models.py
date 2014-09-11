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

from datetime import datetime
from functools import wraps

from main import r

def flushdb():
    """
    Prepare the database to store users.
    """
    r.set("message_last_id", 0)    

def exists(f):
    """
    Raises an exception if the user does not exist.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not r.exists(self.key):
            raise ValueError(
                "Object %s does not exist in the database." % self.key
            )
        return f(self, *args, **kwargs)
    return wrapper

def not_exists(f):
    """
    Raises an exception if the user exists.
    """
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if r.exists(self.key):
            raise ValueError(
                "Object %s already exists in the database." % self.key
            )
        return f(self, *args, **kwargs)
    return wrapper

class DBModel(object):
    """
    Representation of a database object.
    """
    def __init__(self, obj_type, obj_id):
        """
        Creates a new object with the following data:
        * obj_type - Object type
        * obj_id - Object ID

        The object will be located at "obj_type:obj_id"
        after it is created. The key of the object can
        be accessed using `obj.key`.
        """
        self.type = obj_type
        self.id = obj_id
        self.key = "%s:%s" % (self.type, self.id)

        self.created_at = None

    @not_exists
    def new(self):
        """
        Creates a new object in the database.
        """
        self.created_at = datetime.now()
        for k, v in self.__dict__.iteritems():
            self.set(k, v)

    @exists
    def delete(self):
        """
        Delete the object in the database.
        """
        r.delete(self.key)

    @exists
    def get(self):
        """
        Returns user information.
        """
        return r.hgetall(self.key)

    def set(self, field, value):
        """
        Sets object information given a field
        and value.
        """
        setattr(self, field, value)
        r.hset(self.key, field, value)

    @exists
    def load(self):
        """
        Load object information from the database.
        """
        for k, v in self.get().iteritems():
            setattr(self, k, v)

class Message(DBModel):
    """
    Class representing a message.
    """

    def __init__(self, msg_id, sender="", content="", stamp=datetime.now()):
        """
        Creates a message given the ID of the message.

        Optional Parameters:
        * sender - Username of the sender.
        * content - Content of the message.
        * stamp - Timestamp of the message.
                  Default is the current time.
        """
        DBModel.__init__(self, "message", msg_id)
        self.sender = sender
        self.content = content
        self.stamp = stamp

    @exists
    def send_users(self, users):
        """
        Send a list of users the message.
        """
        r.set("%s:count" % self.key, len(users))
        for username in users:
            user = User(username)
            r.rpush("%s:queue" % user.key, self.key)

    @exists
    def recieved(self):
        """
        Mark a message to be recieved by a user.
        """
        val = r.decr("%s:count" % self.key)
        if val == 0:
            r.delete("%s" % self.key)
            r.delete("%s:count" % self.key)

class User(DBModel):
    """
    Class representing User object.
    """

    def __init__(self, username, email="", phone_no=""):
        """
        Creates a user given the following parameters:
        * username - Username of the user.

        Optional parameters:
        * email - Email address of the user.
        * phone_no - Phone number of the user.
        """
        DBModel.__init__(self, "user", username)
        self.email = email
        self.phone_no = phone_no

class Group(DBModel):
    """
    Class representing a group.
    """

    def __init__(self, groupname):
        """
        Creates a group given the following parameters:
        * groupname - Shortname of the group.
        """
        DBModel.__init__(self, "group", groupname)
