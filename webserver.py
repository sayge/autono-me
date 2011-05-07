#!/usr/bin/python
#    This file is part of autono:me - a set of tools to manipulate encrypted 
#    social networking files
#    (C) 2011, by its creators
#
#    autono:me is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autono:me is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autono:me. If not, see <http://www.gnu.org/licenses/>.
from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse, urllib
import autonome
import logging
import getopt
import platform, os, os.path, sys
import ConfigParser
import cgi
import re
from threading import Thread
import json, time,  datetime
import autonometemplate

autonomeobj = None
loadremotesharethread = None
passwordisset = False
cachedpassword = ""


CONSTWEBSERVERREFRESHTHREADMINUTES = 15


class Template():

	filename = None
	values = {}

	def __init__(self, filename):
		self.filename = filename

	def set(self, key, value):
		self.values[key] = value

	def result(self):
		t = autonometemplate.get_template(self.filename)


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
	

	def __init__(self, autonomeobj, myprofile, password=""):
		Thread.__init__(self)
		self.autonomeobj = autonomeobj
		self.myprofile = myprofile
		#TODO das in einen extra-thread auslagern
		try:
			self.privatekey = self.autonomeobj.load_private_key(password)
		except:
			pass

	def run(self):
		if self.privatekey != None:
			fn = self.autonomeobj.get_config("Files", "RemoteCache", self.autonomeobj.profiledir + os.sep + "RemoteCache")
			self.remotesharecache = self.autonomeobj.get_cachefile(fn, self.privatekey)
			self.followlist = self.autonomeobj.load_followlist(json.loads(self.myprofile["pubkey"].decode("hex")))

			while True:
				self.refresh()
				time.sleep(60 * CONSTWEBSERVERREFRESHTHREADMINUTES)

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
			if autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None))) != None:
				profilefound = True
		return profilefound



	def doCreateProfileForm(self, errors = ""):
		template = Template("createprofileform.tpl")
		template.set("errors", errors)
		return template.cleanresult()


	def doSetPasswordForm(self):
		template = Template("setpasswordform.tpl")
		return template.cleanresult()

	def doCreateProfile(self, form):
		name = form['name'].value
		email = form['email'].value
		if name == "" or email == "":
			return self.doCreateProfileForm("Error Message") #TODO
		else:
			if form.has_key("privatekeypassword") and form["privatekeypassword"].value!="":
				passwordisset = True
				cachedpassword = form["privatekeypassword"].value
				password = form["privatekeypassword"].value
			else:
				password = ""

			autonomeobj.create_new_fileset(name, email, password)
			template = Template("aftercreateprofile.tpl")
			return template.cleanresult()

	def doShowWall(self):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()

		global loadremotesharethread
		template = Template("wall.tpl")
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))

		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		for i in _tags:
			tags.append( { "tagname":i })

		if loadremotesharethread == None or loadremotesharethread.is_alive():
			loadremotesharethread = LoadRemoteShareThread(autonomeobj, myprofile)
			loadremotesharethread.daemon = True
			loadremotesharethread.start()

		posts = []
				
		if loadremotesharethread.remotesharecache != None:
			objs = autonomeobj.return_updates_as_array(loadremotesharethread.remotesharecache)
			for key,value in objs.items():
				text = value["text"]
				urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
				for u in urls:
					text = text.replace(u, "<a href=\""+u+"\">"+u+"</a>")
				posts.append({ "pname":value["name"], "ptext": text,  "dt":datetime.datetime.strptime(value["date"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d.%m.%Y %H:%M:%S")})

		template.set("posts",posts)
		template.set("tags",tags)

		template.set("name", myprofile["name"])
		return template.cleanresult()

	def doShowShareList(self):
		template = Template("sharelist.tpl")
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))

		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		for i in _tags:
			tags.append( { "tagname":i })

		shares = []
		for s in sharelist:
			shares.append({"sname":s["name"],  "url":s["url"],  "tags":",".join(s["tags"])})
		template.set("shares",shares)
		template.set("tags",tags)

		template.set("name", myprofile["name"])
		return template.cleanresult()

	def doShowFollowList(self):
		template = Template("followlist.tpl")
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		followlist = autonomeobj.load_followlist(json.loads(myprofile["pubkey"].decode("hex")))

		follows= []
		for s in followlist:
			follows.append({"fname":s["name"],  "url":s["url"]})
		template.set("follows",follows)

		template.set("name", myprofile["name"])
		return template.cleanresult()

	def doShowEditProfile(self):
		template = Template("editprofile.tpl")
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		
		alturls = []
		for u in myprofile["alternateurls"]:
			alturls.append({"url":u})
		template.set("alturls", alturls)

		template.set("name", myprofile["name"])
		template.set("email", myprofile["email"])

		return template.cleanresult()

	def doSaveProfile(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		if form.has_key("name") and form["name"].value !="":
			autonomeobj.set_name(privatekey, form["name"].value)
		if form.has_key("email") and form["email"].value !="":
			autonomeobj.set_email(privatekey, form["email"].value)

		return self.doShowEditProfile()

	def doAddAltURL(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		if form.has_key("url") and form["url"].value !="":
			autonomeobj.add_alt_url(privatekey, form["url"].value)
		return self.doShowEditProfile()

	def doRemoveAltURL(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		if form.has_key("url") and form["url"].value !="":
			autonomeobj.remove_alt_url(privatekey, form["url"].value)
		return self.doShowEditProfile()

	def doAddShare(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
		_tags = autonomeobj.get_tags(sharelist)
		tags = []
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

	def doAddFollow(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		followlist = autonomeobj.load_followlist(json.loads(myprofile["pubkey"].decode("hex")))
		
		url= form['url'].value

		followlist = autonomeobj.follow_stream(followlist, url)
		autonomeobj.save_followlist(privatekey, followlist)

		return self.doShowFollowList()

	def doUnfollow(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		followlist = autonomeobj.load_followlist(json.loads(myprofile["pubkey"].decode("hex")))
		
		url= form['url'].value

		followlist = autonomeobj.unfollow_stream(followlist, url)
		autonomeobj.save_followlist(privatekey, followlist)

		return self.doShowFollowList()

	def doUnshare(self, form):
		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream("file://"+urllib.pathname2url(autonomeobj.get_config("Files", "PublicStream", None)))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
		
		url= form['url'].value

		sharelist = autonomeobj.unshare(sharelist, url)
		autonomeobj.save_sharelist(privatekey, sharelist)

		return self.doShowShareList()

	def doSetPassword(self, form):
		global passwordisset
		global cachedpassword
		if form.has_key("privatekeypassword") and form["privatekeypassword"].value!="":
			passwordisset = True
			cachedpassword = form["privatekeypassword"].value
			return self.doShowWall()
		else:
			return self.doSetPasswordForm()

	def doPostStatus(self, form):

		if passwordisset:
			try:
				privatekey = autonomeobj.load_private_key(cachedpassword)
			except:
				return self.doSetPasswordForm()
		else:
			privatekey = autonomeobj.load_private_key()
		(myprofile, myshares) = autonomeobj.load_and_check_publicstream(autonomeobj.get_config("file://"+urllib.pathname2url("Files", "PublicStream", None)))
		sharelist = autonomeobj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
		_tags = autonomeobj.get_tags(sharelist)
		tags = []
		for i in _tags:
			if form.has_key(i) and form[i].value == "1":
				tags.append(i)
				
		if form.has_key("sharepublic") and form["sharepublic"].value=="public":
			tags.append("public")

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

		if autonomeobj.get_config("Settings", "EncryptPrivateKey", "false") != "false" and passwordisset == False:
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doSetPasswordForm()) 
			return

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

		if self.path == "/followlist":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(self.doShowFollowList())		       
			return

		if self.path == "/editprofile":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(self.doShowEditProfile())		       
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

		if self.path == '/postsetpasswordform':	#this before enterpasswordform
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doSetPassword(form)) 
			return

		if autonomeobj.get_config("Settings", "EncryptPrivateKey", "false") != "false" and passwordisset == False:
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doSetPasswordForm()) 
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
		if self.path == '/unshare':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doUnshare(form))
			return
		if self.path == '/saveprofile':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doSaveProfile(form))
			return
		if self.path == '/addalturl':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doAddAltURL(form))
			return
		if self.path == '/removealturl':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doRemoveAltURL(form))
			return
		if self.path == '/addfollow':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doAddFollow(form))
			return
		if self.path == '/unfollow':	
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(self.doUnfollow(form))
			return

		return


if __name__ == '__main__':
	from BaseHTTPServer import HTTPServer
	logging.basicConfig(level=logging.DEBUG)

	templatedir = sys.path[0] + os.sep + "templates"


	profiledir = None
	port = 8082
	optlist, args = getopt.getopt(sys.argv[1:], "d:p:", ["profiledirectory=","port="])
	for o, a in optlist:
		if o in ("-d", "--profile-directory"):
			profiledir = a
		if o in ("-p", "--port"):
			try:
				if int(a) > 1024:
					port = int(a)
				else:
					logging.error("Port number too small. Try larger than 1024")
			except ValueError:
				logging.error("Invalid port number argument.")
				pass


	if profiledir != None and profiledir[-1] == "/":
		profiledir = profiledir[:-1]


	autonomeobj = autonome.Autonome(profiledir)

	server = HTTPServer(('localhost', port), GetHandler)
	print "Profile directory is set to "+autonomeobj.profiledir
	print "Use the -d <dir> option to change."
	print "Starting webserver. Point your browser to http://127.0.0.1:"+str(port)+"/ to get started."
	print "Use the -p <number> option to change local port number."
	print "Ctrl-C to exit."
	server.serve_forever()

