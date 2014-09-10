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

from main import r

def init_db():
    """
    Initialize the database.
    """
    r.flushdb()

class User(object):
    def __init__(self, username):
        """
        Takes in the following parameters:
        * username - Username of the user
        """
        self.username = username

        self.groups = set()

    def info(self):
        """
        Returns the user information.
        """
        data = self.__dict__
        data.pop("username")
        data["groups"] = list(self.groups)
        return data

class Group(object):
    def __init__(self, groupname):
        """
        Takes in the following parameters:
        * groupname - Shortname of the group
        """
        self.groupname = groupname

        self.members = set()

    def info(self):
        """
        Returns the group information.
        """
        data = self.__dict__
        data.pop("groupname")
        data["members"] = list(self.members)
        return data

def new_user(user):
    """
    Creates a user given an instance
    of the User class.
    """
    if r.exists("user:%s" % user.username):
        raise ValueError("User with the same username exists.")

    for k, v in user.info().iteritems():
        r.hset("user:%s" % user.username, k, v)

def new_group(group):
    """
    Creates a group given an instance
    of the Group class.
    """
    if r.exists("group:%s" % group.groupname):
        raise ValueError("Group with the same groupname exists.")

    for k, v in group.info().iteritems():
        r.hset("group:%s" % group.groupname, k, v)

def get_user(username):
    """
    Returns a user given the username.
    """
    if not r.exists("user:%s" % username):
        raise ValueError("User does not exist.")

    user_info = r.hgetall("user:%s" % username)
    user = User(username)
    for key, val in user_info.iteritems():
        setattr(user, key, val)
    return user

def get_group(groupname):
    """
    Returns a group given the name of the group.
    """
    if not r.exists("group:%s" % groupname):
        raise ValueError("Group does not exist.")

    group_info = r.hgetall("group:%s" % groupname)
    group = Group(groupname)
    for key, val in group_info.iteritems():
        setattr(group, key, val)
    return group
