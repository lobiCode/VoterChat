
import cherrypy # CherryPy lightweight webframework. Install with: sudo pip install cherrypy
import datetime
import collections

# TODO: Expire users who haven't polled in a while, or set their status to 'away'.
# TODO: Expire messages older than X days.
        
class Message(object):
    def __init__(self, sender, recipient, message):
        self.sender = sender
        self.recipient = recipient
        self.stamp = datetime.datetime.now()
        self.message = message
        self.delivered = False
        
class Group(object):
    def __init__(self, name):
        self.name = name
        self.members = set() # Users in this group.
        self.messages = [] # Messages which still have to be delivered to members of this group.

        
groups = {} # Known groups, mapping from groupname -> Group instance
users = collections.defaultdict(set) # Known users, mapping from username -> Group instances they're in


def join(data):
    """Process the join command"""
    if "group" not in data:
        return {"result": "error", "message": "group parameter missing"}
    if "user" not in data:
        return {"result": "error", "message": "user parameter missing"}
    username = data["user"]
    groupname = data["group"] # TODO check for empty strings    
    note = ""
    if groupname in groups:
        group = groups[groupname]
        if username in group.members:
            note = "You are already in the group '%s'" % groupname
        else:
            group.members.add(username)
            users[username].add(group)
            note = "You have been added to the group '%s', which now has %d users." % (groupname, len(group.members))
    else:
        # Group doesn't exist yet. Create a new group with the given name, and put the user in it.
        group = Group(groupname)
        groups[groupname] = group
        group.members.add(username)
        users[username].add(group)
        note = "You have created a new group '%s'" % groupname
    return {"result": "success", "note": note}
    
    
def poll(data):
    """Process the poll command"""
    if "user" not in data:
        return {"result": "error", "message": "user parameter missing"}
    # See what queued messages should be returned.
    username = data["user"]
    if username not in users:
        return {"result": "error", "message": "unknown user, or not in any groups"}
    content = []
    for group in users[username]:
        for msg in group.messages:
            if msg.recipient == username:
                content.append((msg.sender, group.name, msg.message))
                msg.delivered = True
    # Prune delivered messages. TODO: Also expire messages that are too old.
    group.messages = [msg for msg in group.messages if not msg.delivered]
    return {"result": "success", "messages": content} # list of tuples of ("from", "group", "message")
    

def send(data):
    """Process the send command"""
    if "group" not in data:
        return {"result": "error", "message": "group parameter missing"}
    if "user" not in data:
        return {"result": "error", "message": "user parameter missing"}
    if "message" not in data:
        return {"result": "error", "message": "message parameter missing"}
    username = data["user"]
    groupname = data["group"]
    message = data["message"]
    # Check if the group exists.
    if groupname not in groups:
        return {"result": "error", "message": "group '%s' doesn't exist" % groupname}
    # Check if the user is in the group.
    group = groups[groupname]
    if username not in group.members:
        return {"result": "error", "message": "you are not in group '%s'" % groupname}
    # Create a Messages for all other members of this group.
    for member in group.members:
        if member == username:
            continue # Don't send messages to ourself.
        msg = Message(username, member, message)
        group.messages.append(msg)
    return {"result": "success"}


def list(data):
    """Process the list command"""    
    grouplist = []
    for groupname in sorted(groups.keys()):
        group = groups[groupname]
        grouplist.append("%s: %d users" % (groupname, len(group.members)))
    return {"result": "success", "groups": grouplist}
    
    
class VoterChat(object):
    """Simple webapp that only accepts POSTs of JSON and diverts them to a processing function. Also returns JSON to the client."""
    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()    
    def api(self):
        if cherrypy.request.method != "POST":
            raise cherrypy.HTTPError(405) # Only accept POST requests.
        data = cherrypy.request.json
        command = data["command"]
        if command in ("join", "send", "poll", "list"): # , kick, leave, etc...
            result = globals()[command](data)
        else:
            result = {"result": "error", "message": "unknown or missing command"}
        return result        
        
        
if __name__ == "__main__":
    print "\n\nNow start one or more clients using 'python client.py' and join a group on this server using the 'join' command.\n\n"
    conf = {"/": {}}
    cherrypy.quickstart(VoterChat(), "/", conf)
