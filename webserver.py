from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import autonome
import logging
import getopt
import platform, os, os.path, sys
import ConfigParser
import cgi
import re
from threading import Thread
import json, time,  datetime

templatedir = None
autonomeobj = None
loadremotesharethread = None

todo = """
	3. create_profile_form -> name, e-mail
		-> create profile + display instructions
	4. "/" -> display messages
	5. edit_profile / edit_profile_handle
	6. add_friend
	7. share_with_friend
	8. list_friends
	9. post_message
	10. download public profile
	11. extensive help

"""


class Template():

	filename = None
	values = {}

	def __init__(self, filename):
		self.filename = filename

	def set(self, key, value):
		self.values[key] = value

	def result(self):
		f = open(templatedir + os.sep + self.filename, "r");
		t = f.read()
		f.close()

		#include files in templates with {include example.tpl}
		incre = re.compile("\{include [^\}]+\}")
		tre = t
		for i in incre.findall(t):
			t2 = Template(i[8:-1].strip())
			tre = tre.replace(i, t2.result())
		t = tre


		#set parent template with {parent example.tpl}
		#in parent template contents of current template will be inserted as the variable
		#CHILD
		incre = re.compile("\{parent [^\}]+\}")
		m = incre.match(t)
		if m:
			t2 = Template(m.group()[7:-1].strip())
			t2.set("child", t.replace(m.group(), ""))
			t = t2.result();

		repre = re.compile("\{repeat ([^\}]+)\}([^\{]+)\{end\}")
		for key, value in self.values.items():
			if type(value) == type(list()):
				t2 = t
				iterator = repre.finditer(t)
				for match in iterator:
					if match.group(1) == key.upper():
						content = match.group(2)
						newcontent = ""
						for i in value:
							newcontent2 = content
							for key2, value2 in i.items():
								newcontent2 = newcontent2.replace("#"+key2.upper()+"#", value2)
							newcontent = newcontent+newcontent2
						t2 = t2.replace(match.group(0), newcontent)
				t = t2
			else:
				t = t.replace("#"+key.upper()+"#", value) #TODO repeatables
		return t

	def cleanresult(self):
		"""provides the template content with all unset variables stripped out"""
		s = self.result()
		s2 = s
		pre = re.compile("#[A-Z]+#")
		for i in pre.findall(s):
			s2 = s2.replace(i,"")
		return s2


class LoadRemoteShareThread(Thread):

	autonomeobj = None
	remotesharecache = None
	sharecache = None
	myprofile = None
	followlist = None
	privatekey = None
	stream = []
	posts = []

	def __init__(self, autonomeobj, myprofile):
		Thread.__init__(self)
		self.autonomeobj = autonomeobj
		self.myprofile = myprofile
		#TODO das in einen extra-thread auslagern
		self.privatekey = self.autonomeobj.load_private_key()


	def run(self):
		fn = self.autonomeobj.get_config("Files", "RemoteCache", self.autonomeobj.profiledir + os.sep + "RemoteCache")
		self.remotesharecache = self.autonomeobj.get_cachefile(fn, self.privatekey)
		self.followlist = self.autonomeobj.load_followlist(json.loads(self.myprofile["pubkey"].decode("hex")))

		while True:
			self.refresh()
			time.sleep(60 * 15)

	def refresh(self):
		fn = self.autonomeobj.get_config("Files", "RemoteCache", self.autonomeobj.profiledir + os.sep + "RemoteCache")
		self.remotesharecache = self.autonomeobj.get_updates(self.privatekey, self.remotesharecache, self.followlist)
		self.stream = self.autonomeobj.return_updates_as_array(self.remotesharecache)
		self.autonomeobj.save_cachefile(fn, self.remotesharecache, json.loads(self.myprofile["pubkey"].decode("hex")))

		self.posts = []
		for key in sorted(self.stream.iterkeys(),  reverse=True):
			self.posts.append({ "contact": self.stream[key]["name"], "content": self.stream[key]["text"] })


class GetHandler(BaseHTTPRequestHandler):
	privatekey = None
	wallposts = []
	loadremotesharethread = None
	#TODO verlagern von autonomeobj in klasse

	def check(self):
		profilefound = False
		if autonomeobj.get_config("Files", "PublicStream", None) != None:
			if autonomeobj.load_and_check_publicstream(autonomeobj.get_config("Files", "PublicStream", None)) != None:
				profilefound = True
		return profilefound


	#TODO Handler fuer Form Passwort und Handling Passwort

	def doCreateProfileForm(self, errors = ""):
		template = Template("createprofileform.tpl")
		template.set("errors", errors)
		return template.cleanresult()


	def doCreateProfile(self, form):
		name = form['name'].value
		email = form['email'].value
		if name == "" or email == "":
			return self.doCreateProfileForm("Error Message") #TODO
		else:
			autonomeobj.create_new_fileset(name, email)
			template = Template("aftercreateprofile.tpl")
			return template.cleanresult()

	def doShowWall(self):
		global loadremotesharethread
		template = Template("wall.tpl")
		print "Load profile"
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream(autonomeobj.get_config("Files", "PublicStream", None))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))

		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		for i in _tags:
			tags.append( { "tagname":i })

		if loadremotesharethread == None:
			loadremotesharethread = LoadRemoteShareThread(autonomeobj, myprofile)
			loadremotesharethread.daemon = True
			loadremotesharethread.start()

		posts = []
				
		if loadremotesharethread.remotesharecache != None:
			objs = autonomeobj.return_updates_as_array(loadremotesharethread.remotesharecache)
			for key,value in objs.items():
				posts.append({ "pname":value["name"], "ptext": value["text"],  "dt":datetime.datetime.strptime(value["date"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d.%m.%Y %H:%M:%S")})

		template.set("posts",posts)
		template.set("tags",tags)

		template.set("name", myprofile["name"])
		return template.cleanresult()

	def doShowShareList(self):
		template = Template("sharelist.tpl")
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream(autonomeobj.get_config("Files", "PublicStream", None))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))

		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		for i in _tags:
			tags.append( { "tagname":i })

		shares = []
		for s in sharelist:
			shares.append({"name":s["name"],  "url":s["url"],  "tags":",".join(s["tags"])})
		template.set("shares",shares)
		template.set("tags",tags)

		template.set("name", myprofile["name"])
		return template.cleanresult()


	def doAddShare(self, form):
		privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream(autonomeobj.get_config("Files", "PublicStream", None))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		print form
		for i in _tags:
			if form.has_key(i) and form[i].value == "1":
				tags.append(i)
		
		if form.has_key("newtags"):
			if form["newtags"].value!="":
				if "," in form["newtags"].value:
						for j in form['newtags'].value.split(","):
							if j.strip().lower() !="":
									tags.append(j.strip() .lower())
				else:
					tags.append(form["newtags"].value.strip().lower())

		url= form['url'].value

		sharelist = autonomeobj.share_stream(sharelist, url, tags)
		autonomeobj.save_sharelist(privatekey, sharelist)

		return self.doShowShareList()


	def doPostStatus(self, form):

		privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream(autonomeobj.get_config("Files", "PublicStream", None))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		print form
		for i in _tags:
			if form.has_key(i) and form[i].value == "1":
				tags.append(i)

		status = form['status'].value

		fn = autonomeobj.get_config("Files", "LocalCache", autonomeobj.profiledir + os.sep + "LocalCache")
		sharecache = autonomeobj.get_cachefile(fn, privatekey)
		sharecache = autonomeobj.publish_text_message(privatekey, sharecache, myprofile, sharelist, status, tags)
		autonomeobj.save_cachefile(fn, sharecache, json.loads(myprofile["pubkey"].decode("hex")))

		return self.doShowWall()


	def getStaticfile(self, filename):
		f = open(os.curdir + os.sep + "static" + os.sep + filename)
		s = f.read()
		f.close()
		return s
    
	def do_GET(self):
		if self.client_address[0] != "127.0.0.1":
			return

		if not self.check():
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doCreateProfileForm())
			return

		#TODO check for encrypted private key
		if self.path == "/":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(self.doShowWall())		       
			return

		if self.path == "/sharelist":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(self.doShowShareList())		       
			return

		if self.path == "/stopserver":

			sys.exit()
			return


		if self.path.startswith("/static"):
			self.send_response(200)
			self.end_headers()
			self.wfile.write(self.getStaticfile(self.path[7:]))
			return
			

		self.send_response(404)
		return

	def do_POST(self):
		if self.client_address[0] != "127.0.0.1":
			return
		# Parse the form data posted
		form = cgi.FieldStorage(
		    fp=self.rfile, 
		    headers=self.headers,
		    environ={'REQUEST_METHOD':'POST',
		             'CONTENT_TYPE':self.headers['Content-Type'],
		             })

		if self.path == '/postcreateform':	#this before check
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doCreateProfile(form))
			return
				
		if not self.check():
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doCreateProfileForm())
			return

		if self.path == '/poststatus':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doPostStatus(form))
			return
		if self.path == '/addshare':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doAddShare(form))
			return

		return


if __name__ == '__main__':
	from BaseHTTPServer import HTTPServer
	logging.basicConfig(level=logging.DEBUG)

	templatedir = sys.path[0] + os.sep + "templates"


	profiledir = None
	optlist, args = getopt.getopt(sys.argv[1:], "d:", ["profiledirectory="])
	for o, a in optlist:
		if o in ("-d", "--profile-directory"):
			profiledir = a

	#TODO Option for different port number

	autonomeobj = autonome.Autonome(profiledir)

	server = HTTPServer(('localhost', 8080), GetHandler)
	print "Profile directory is set to "+autonomeobj.profiledir
	print "Use the -d <dir> option to change."
	print "Starting webserver. Point your browser to http://127.0.0.1:8080/ to get started."
	print "Ctrl-C to exit."
	server.serve_forever()

