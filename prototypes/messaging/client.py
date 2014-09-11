
import requests # HTTP Requests library. Install with: sudo pip install requests
import cmd
import random
import json

username = "User" + str(int(random.uniform(10000,90000)))
print "Your username is", username

serverurl = "http://localhost:8080/api"
print "Using the server", serverurl


def sendcommand(command, groupname=None, message=None):
    data = {"user": username, "command": command}
    if groupname:
        data.update({"group": groupname})
    if message:
        data.update({"message": message})
    try:
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        r = requests.post(serverurl, data=json.dumps(data), headers=headers)
    except requests.exceptions.ConnectionError:
        return 0, "Error: Can't connect to server. You need to run the server first, using 'python server.py'"
    return r.status_code, json.loads(r.text)


class Client(cmd.Cmd):
    def __init__(self, name=""):
        self.intro = "Type '?' for a list of commands. The commands are:\n" \
            "join <group>             Join an existing group, or form a new one.\n" \
            "list                     Show which groups are available on the server.\n" \
            "poll                     See if there are any new messages for you.\n" \
            "send <group> <message>   Send a message to a group.\n" \
            "quit                     Quit this client.\n\n" \
            "Press Enter every ten seconds or so, to simulate a poll.\n"
        cmd.Cmd.__init__(self)
        
    def default(self, arg):
        print "Unrecognizable command. Type 'help' or '?' for a list of commands."

    def do_quit(self, arg):
        pass
        
    def do_join(self, groupname):
        status, response = sendcommand("join", groupname)
        print status, response
        
    def do_poll(self, arg=None):
        status, response = sendcommand("poll")
        print status, response
        if status == 200 and "messages" in response:
            print "\nYou got messages:\n"
            for msg in response["messages"]:
                sender, group, message = msg
                print "From %s@%s: %s" % (sender, group, message)
            print
        
    def emptyline(self): # Just pressing Enter is a shortcut for 'poll'.
        self.do_poll()
        
    def do_list(self, arg=None):
        status, response = sendcommand("list")
        print status, response
        
    def do_send(self, arg):
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print "Usage: send groupname message"
            return
        groupname, message = parts
        status, response = sendcommand("send", groupname, message)
        print status, response
        
    def postcmd(self, stop, line):
        if line in ("q", "quit"):
            return True        

    do_q = do_quit
    do_j = do_join
    do_l = do_list
    do_s = do_send
    
if __name__ == "__main__":
    client = Client()
    client.prompt = "%s > " % username
    client.cmdloop()