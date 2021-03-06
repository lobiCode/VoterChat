
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

class Election(object):
    def __init__(self, kind, username, groupname):
        self.kind = None # "invite", "kick" or "concluded"
        self.until = datetime.datetime.now() + datetime.timedelta(minutes=2) # Expiration date/time.
        self.yesvotes = 0
        self.novotes = 0
        self.voters = set() # Users who have already voted in this election
        self.username = username # Who is this vote about?
        self.groupname = groupname # And what group does the votee wants to join (or, from which group should he be kicked?)

        
groups = {} # Known groups, mapping from groupname -> Group instance
users = collections.defaultdict(set) # Known users, mapping from username -> Group instances they're in
elections = {} # Active elections, mapping from (groupname, username) -> Election instance

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
            # See if an identical election is in progress.
            key = (groupname, username)
            if key in elections:
                note = "An election for user '%s', group '%s' is already in progress" % (username, groupname)
                return {"result": "error", "note": note}
            # Initiate an election for user to join the group.
            election = Election("invite", username, groupname)
            elections[key] = election
            # Send an appropriate message to users in this group.
            expiration = election.until.strftime("%H:%M:%S")
            message = "User '%s' has asked to join the group '%s'. Use yes or no to vote for it. This election will run until %s" % (username, groupname, expiration)
            for member in group.members:
                msg = Message("system", member, message)
                group.messages.append(msg)
            # And also let the user who wants to join the group know about it
            note = "Your join request has been send to %d member(s) of '%s'. This election will run until %s" % (len(group.members), groupname, expiration)
    else:
        # Group doesn't exist yet. Create a new group with the given name, and put the user in it.
        group = Group(groupname)
        groups[groupname] = group
        group.members.add(username)
        users[username].add(group)
        note = "You have created a new group '%s'" % groupname
    return {"result": "success", "note": note}
    
    
def poll(data):
    """Process the poll command."""
    if "user" not in data:
        return {"result": "error", "message": "User parameter missing"}
    # See what queued messages should be returned.
    username = data["user"]    
    if username not in users:
        users[username] = set()
        return {"result": "error", "message": "You are not in any groups. Use the join command first"}

    # See if this user was engaged in election(s), and if so, if it has been concluded yet.
    for key, election in elections.iteritems():
        if election.username == username:
            concluded = False
            # Has the expiry date/time been reached?
            if datetime.datetime.now() > election.until:
                concluded = True
            # If more than 60% of the group members have voted, that's a conclusion, too.
            groupname = election.groupname
            group = groups[groupname]
            if len(group.members):
                turnout = float(election.yesvotes + election.novotes) / len(group.members) * 100
            else:
                turnout = 100
            print "Turnout:", turnout
            if turnout >= 60:
                concluded = True
            # The verdict?
            if concluded:
                if election.yesvotes >= election.novotes:
                    # It's a YES.
                    if election.kind == "invite":
                        group.members.add(username)
                        users[username].add(group)
                        note = "You have been added to the group '%s', which now has %d users" % (groupname, len(group.members))
                    elif election.kind == "kick":
                        pass # TODO
                else:
                    # It's a NO.
                    if election.kind == "invite":
                        note = "You have been denied access to the group '%s'" % groupname
                    elif election.kind == "kick":
                        note = "The vote to kick you from %s has failed" % groupname
                election.kind = "concluded"
                # TODO: Send note as message to user
                del elections[key] # TODO: global sweep outside of this loop, notify users who are still online that their invitation was terminated without conclusion.

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
        return {"result": "error", "message": "Group parameter missing"}
    if "user" not in data:
        return {"result": "error", "message": "User parameter missing"}
    if "message" not in data:
        return {"result": "error", "message": "Message parameter missing"}
    username = data["user"]
    groupname = data["group"]
    message = data["message"]
    # Check if the group exists.
    if groupname not in groups:
        return {"result": "error", "message": "Group '%s' doesn't exist" % groupname}
    # Check if the user is in the group.
    group = groups[groupname]
    if username not in group.members:
        return {"result": "error", "message": "You are not in group '%s'" % groupname}
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
        if command in ("join", "send", "poll", "list", "invite", "yes", "no"):
            result = globals()[command](data)
        else:
            result = {"result": "error", "message": "Unknown or missing command"}
        return result        
        
        
if __name__ == "__main__":
    print "\n\nNow start one or more clients using 'python client.py' and join a group on this server using the 'join' command.\n\n"
    conf = {"/": {}}
    cherrypy.quickstart(VoterChat(), "/", conf)
