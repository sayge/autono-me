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

import json
import rsa
import Blowfish
import hashlib
import random
import datetime
import logging
import getopt
import platform, os, os.path, sys
import ConfigParser
import urllib

PROGRAMNAME = "autonome"
DEBUG = True
KEYSIZE = 1024
FORMATVERSION = 1
LOCALEXPIRE = 30

class Autonome():

	config = None
	profiledir = "."

	def __init__(self, profiledir = None):

		if profiledir == None:
			if platform.system() == "Windows":
				#Windows code:
				profiledir = os.path.join(os.getenv("APPDATA"), PROGRAMNAME)
			else:
				#Linux and Mac code:
				profiledir = os.path.expanduser("~") + os.sep + ".local" + os.sep + "share" + os.sep + PROGRAMNAME

		if not os.path.isdir(profiledir):
			os.makedirs(profiledir)
		if not os.path.isdir(profiledir + os.sep + "public"):
			os.makedirs(profiledir + os.sep + "public")

		logging.debug("Using profile directory: "+profiledir)
		self.profiledir = profiledir

		settingsfile = profiledir + os.sep + "settings.ini"
	
		self.config = ConfigParser.ConfigParser()
		self.config.read(settingsfile)
		if not self.config.has_section("Files"):
			self.config.add_section("Files")
		if not self.config.has_section("Settings"):
			self.config.add_section("Settings")


	def get_config(self, section, name, default):
		try:
			if self.config.get(section, name) != None:
				return self.config.get(section, name)
		except:
			pass
		self.config.set(section, name, default)
		return default

	def save_config(self):
		with open(self.profiledir+os.sep+"settings.ini", 'wb') as configfile:
		    self.config.write(configfile)

	def load_private_key(self):	#TODO handle password protection
		keyfilef = open(self.get_config("Files", "PrivateKey", None) , "r")
		s = keyfilef.read()
		decodedjson = s.decode("hex")
		privatekey = json.loads(decodedjson)
		return privatekey

	def get_cachefile(self, filename, privatekey):
		""" Load and return items from a cache file
		In cachefiles the locally published messages and the messages from other users are cached
		encrypted with the local user's key pair """
		try:
			f = open(filename, "r")
			s = f.read()
			f.close()
			jsono = rsa.decrypt(s, privatekey)
			o = json.loads(jsono)
		except:
			o = []
		return o

	def save_cachefile(self, filename, cacheobject, publickey):
		""" Save items to a cache file
		In cachefiles the locally published messages and the messages from other users are cached
		encrypted with the local user's key pair """
		try:
			jsons = json.dumps(cacheobject)
			encs = rsa.encrypt(jsons, publickey)
			f = open(filename, "w")
			f.write(encs)
			f.close()
		except IOError, e:
			logging.warning(e)

	def save_publicstream(self, privatekey, profile, shares):
		""" Save the profile and the shares to a public stream file """
		f = open(self.get_config("Files", "PublicStream", "." + os.sep + "public" + os.sep + profile["id"]+".publicstream"), "w")
		profiles = json.dumps(profile)
		profilem = hashlib.md5()
		profilem.update(profiles)
		profilesignature = rsa.sign(profilem.hexdigest(), privatekey)

		#create JSON object
		obj = {  "version": FORMATVERSION, "shares": shares, "profile": profiles, "profilesignature":profilesignature}
		json.dump(obj,f)
		f.close()

	def load_and_check_publicstream(self, filename):
		""" Load profile information and share objects from a given file
		The file is also checked for cryptographic consistency
		filename can either be a local filename or an URL """
		# get the JSON object from the file
		f = urllib.urlopen(filename)
		obj = json.load(f)

		#(0) check format version to ensure forward compatibility
		if obj["version"] != FORMATVERSION:
			return (False, False)

		good = True

		# (1) load profile
		profile = json.loads(obj["profile"])

		# (2) check whether key and id match
		pubkeym = hashlib.md5()
		pubkeym.update(profile["pubkey"])
		good = good and (pubkeym.hexdigest() == profile["id"])

		if (pubkeym.hexdigest() == profile["id"]):
			logging.debug("Check stream "+filename+": ID and Key match")

		# (3) check whether user has signed the profile hash
		pubkey_unhex = profile["pubkey"].decode("hex")
		pubkey = json.loads(pubkey_unhex)

		profilem = hashlib.md5()
		profilem.update(obj["profile"])
		profilehash = profilem.hexdigest()

		v = (rsa.verify(str(obj["profilesignature"]), pubkey) == profilehash)

	
		if v:
			logging.debug("Check stream "+filename+": Profile Hash is signed correctly")
	
		good = good and v 
		if good:
			return (profile, obj["shares"])
		else:
			return (False, False)


	def create_new_fileset(self, name, email, password="", alternateurls=[]): #TODO encrypt private key
		""" setup new keys and the respective files for a user """
		logging.info("Generating RSA Keys. This may take some time...")
		(pub, priv) = rsa.newkeys(KEYSIZE)

		# Private and public key are dumped into json strings
		# then hex-encoded
		# if a password is provided, the private key is Blowfish encrypted with an
		# MD5 hash of this password

		if password !="":
			print "Blowfish encrypting private key"
			m = hashlib.md5()
			m.update(password)
			cipher = Blowfish.Blowfish(m.hexdigest())
			privatekey = cipher.encryptCTR(json.dumps(priv).encode("hex"))
		else:
			privatekey = json.dumps(priv).encode("hex")

		publickey = json.dumps(pub).encode("hex")

		#generate a user id (= MD5 hash of the converted public key)
		useridm = hashlib.md5()
		useridm.update(publickey)
		userid = useridm.hexdigest()

		# save the public and the private key
		privatekeyfilename = self.get_config("Files", "PrivateKey", self.profiledir + os.sep + userid+".privatekey")
		privatekeyfile = open(privatekeyfilename, "w")
		privatekeyfile.write(privatekey)
		privatekeyfile.close()
		self.config.set("Files", "PrivateKey", privatekeyfilename)
		logging.info("Saving private key to "+privatekeyfilename)

		publickeyfilename = self.get_config("Files", "PublicKey", self.profiledir + os.sep + userid +".publickey")
		publickeyfile = open(publickeyfilename, "w")
		publickeyfile.write(publickey)
		publickeyfile.close()
		self.config.set("Files", "PublicKey", publickeyfilename)
		logging.info("Saving public key to "+publickeyfilename)

		#create profile json
		profile = { "id": userid, "pubkey": publickey, "name": name, "email": email, "alternateurls": alternateurls }
		profiles = json.dumps(profile)

		#create signed hash
		profilem = hashlib.md5()
		profilem.update(profiles)
		profilesignature = rsa.sign(profilem.hexdigest(), priv)

		#create JSON object
		obj = {  "version": FORMATVERSION, "shares": [], "profile": profiles, "profilesignature":profilesignature}

		publicstreamfilename = self.get_config("Files", "PublicStream", self.profiledir + os.sep + "public" + os.sep + userid +".publicstream")
		publicstreamfile = open(publicstreamfilename, "w")
		json.dump(obj,publicstreamfile)
		publicstreamfile.close()
		self.config.set("Files", "PublicStream", publicstreamfilename)
		logging.info("Saving public stream to "+publicstreamfilename)
		self.save_config()

		return userid

	def load_sharelist(self,publickey):
		sharelistfile = self.get_config("Files", "Sharelist", self.profiledir+ os.sep + "sharelist")
		try:
			sharelistf = open(sharelistfile, "r")
			jsons = json.load(sharelistf)
			print jsons
			sharelistf.close()
			sharelistm = hashlib.md5()
			sharelistm.update(jsons["sharelist"])
			if rsa.verify(str(jsons["signature"]), publickey) == sharelistm.hexdigest():
				return json.loads(jsons["sharelist"])
		except IOError, e:
			logging.warning(e)
		return []

	def get_tags(self, sharelist):
		tags = []
		for i in sharelist:
			tags.extend(i["tags"])
		tags = list(set(tags))
		return tags

	def save_sharelist(self, privatekey, sharelist): 
		sharelistfile = self.get_config("Files", "Sharelist", self.profiledir + os.sep + "sharelist")
		sharelistf = open(sharelistfile, "w")
		sharelists = json.dumps(sharelist)
		sharelistm = hashlib.md5()
		sharelistm.update(sharelists)
		obj = { "sharelist": sharelists, "signature": rsa.sign(sharelistm.hexdigest(), privatekey) }
		json.dump(obj, sharelistf)
		sharelistf.close()

	# start sharing with someone
	def share_stream(self, sharelist, remotestream, tags):
		"""Share with profile at URL everything tagged with one of the tags in tags
		This does not retroactively share posts.
		Everything posted so far will not be shared. """
		(remoteprofile, remoteshares) = self.load_and_check_publicstream(remotestream)
		if remoteprofile != False:
			sharelist.append({"id": remoteprofile["id"], "pubkey": remoteprofile["pubkey"], "url": remotestream, "name": remoteprofile["name"], "alternateurls":remoteprofile["alternateurls"], "tags":tags})
			return sharelist
		else:
			logging.warning("Remote profile "+remotestream+" could not be loaded")
			return sharelist

	def unshare(self, sharelist, url):
		"""No longer share with profile at URL
		This does not retroactively unshare posts.
		Shared posts stay shared. """
		newsl = []
		for i in sharelist:
			if i["url"] != url:
				newsl.append(i)
			else:
				logging.info("Removed "+url)
		return newsl

	def add_alt_url(self, privatekey, url):
		(myprofile, myshares) = self.load_and_check_publicstream(self.get_config("Files", "PublicStream", None))
		myprofile["alternateurls"].append(url)
		self.save_publicstream(privatekey, myprofile, myshares)

	def set_name(self, privatekey, name):
		(myprofile, myshares) = self.load_and_check_publicstream(self.get_config("Files", "PublicStream", None))
		myprofile["name"]=name
		self.save_publicstream(privatekey, myprofile, myshares)

	def set_email(self, privatekey, email):
		(myprofile, myshares) = self.load_and_check_publicstream(self.get_config("Files", "PublicStream", None))
		myprofile["email"]=email
		self.save_publicstream(privatekey, myprofile, myshares)

	def remove_alt_url(self, privatekey, url):
		(myprofile, myshares) = self.load_and_check_publicstream(self.get_config("Files", "PublicStream", None))
		try:
			myprofile["alternateurls"].remove(url)
		except ValueError, e:
			logging.info(e)
		self.save_publicstream(privatekey, myprofile, myshares)

	def publish_text_message(self, privatekey, sharecache, profile, sharelist, message, tags=[], public=False): 
		#load and expire cached shares
		shares = []
		for i in range(0, len(sharecache)):
			if sharecache[i]["dt"] > ((datetime.datetime.utcnow() + datetime.timedelta(days=-1*int(self.get_config("Settings", "LocalExpire", LOCALEXPIRE) ) )).isoformat()):
				#NOT EXPIRED
				shares.append(sharecache[i]["content"])
			else:
				sharecache.remove(sharecache[i])

		#pre-encode message-to-be-sent
		#we have it to do with three json objects within each other, oh my!
		shareobj = {"datetime": datetime.datetime.utcnow().isoformat(), "type": "wallpost", "reference": "", "text":message, "attachment":""} 
		shareobjs = json.dumps(shareobj)
	
		shareobjm = hashlib.md5()
		shareobjm.update(shareobjs)
		postid = shareobjm.hexdigest()

		if "public" in tags:
			#A public post, no need for encryption
			content1 = {"recipient":"public", "content": shareobjs, "id": postid}
			content1s = json.dumps(content1)
			content1m = hashlib.md5()
			content1m.update(content1s)
			content1hash = content1m.hexdigest()
			signature = rsa.sign(content1hash, privatekey)

			realcontent = {"content":content1s, "signature":signature}
			realcontents = json.dumps(realcontent)
			shares.append(realcontents)
			sharecache.append( { "dt": datetime.datetime.utcnow().isoformat(), "content": realcontents })
		else:
			#Not a public post, we need to encrypt for each recipient
			for recipient in sharelist:
				shareflag = False
				for i in recipient["tags"]:
					for j in tags:
						if i==j:
							shareflag = True
				if shareflag:
					#print "Found recipient "+recipient["id"]
					content1 = {"recipient":recipient["id"], "content": shareobjs, "id": postid}
					content1s = json.dumps(content1)
					content1m = hashlib.md5()
					content1m.update(content1s)
					content1hash = content1m.hexdigest()
					signature = rsa.sign(content1hash, privatekey)

					realcontent = {"content":content1s, "signature":signature}
					realcontents = json.dumps(realcontent)
					encrypted_string = rsa.encrypt(realcontents, json.loads(recipient["pubkey"].decode("hex")))
					shares.append(encrypted_string)
					sharecache.append( { "dt": datetime.datetime.utcnow().isoformat(), "content": encrypted_string })
                    
			#encode for self
			content1 = {"recipient":profile["id"], "content": shareobjs, "id": postid}
			content1s = json.dumps(content1)
			content1m = hashlib.md5()
			content1m.update(content1s)
			content1hash = content1m.hexdigest()
			signature = rsa.sign(content1hash, privatekey)

			realcontent = {"content":content1s, "signature":signature}
			realcontents = json.dumps(realcontent)
			encrypted_string = rsa.encrypt(realcontents, json.loads(profile["pubkey"].decode("hex")))
			shares.append(encrypted_string)
			sharecache.append( { "dt": datetime.datetime.utcnow().isoformat(), "content": encrypted_string })
            
		self.save_publicstream(privatekey, profile, shares)
		return sharecache			
	
	def load_followlist(self, publickey): 
		followlistfile = self.get_config("Files", "Followlist", self.profiledir + os.sep + "followlist")
		try:
			followlistf = open(followlistfile, "r")
			jsons = json.load(followlistf)
			followlistf.close()
			followlistm = hashlib.md5()
			followlistm.update(jsons["followlist"])
			if rsa.verify(str(jsons["signature"]), publickey) == followlistm.hexdigest():
				return json.loads(jsons["followlist"])			
		except IOError, e:
			logging.warning(e)
		return []

	def save_followlist(self,secretkey, followlist):
		followlistfile = self.get_config("Files", "Followlist", self.profiledir + os.sep + "followlist")
		followlistf = open(followlistfile, "w")
		followlists = json.dumps(followlist, followlistf)
		followlistm = hashlib.md5()
		followlistm.update(followlists)
		signature = rsa.sign(followlistm.hexdigest(), secretkey)
		json.dump( { "followlist":followlists, "signature":str(signature)}, followlistf  )
		followlistf.close()

	# start following someone
	def follow_stream(self, followlist, remotestream):
		try:
			(remoteprofile, remoteshares) = self.load_and_check_publicstream(remotestream)
			if remoteprofile != False:
				followobj = {"id": remoteprofile["id"], "pubkey": remoteprofile["pubkey"], "url": remotestream, "name": remoteprofile["name"], "alternateurls":remoteprofile["alternateurls"], "lastcheck": datetime.datetime.utcnow().isoformat()}
				alreadythere = False
				for i in followlist:
					if i["id"] == followobj["id"]:
							alreadythere = True
				if not alreadythere:
						followlist.append(followobj)
				else:
					logging.warning("URL "+remotestream+"is already in followlist")
			else:
				logging.warning("Remote profile "+remotestream+" could not be loaded.")
		except:
				logging.warning("Error reading remote profile")
            
		return followlist


	def unfollow_stream(self, followlist, url):
		""" Remove an url from the list of followed urls """
		newfl = []
		for i in followlist:
			if i["url"] != url:
				newfl.append(i)
			else:
				logging.info("Removed "+url)
		return newfl

	def addtoremotesharecache(self, remotesharecache, item): #check if an item is not yet in our cache of remote items and adds it if that is the case
		found = False
		for o in remotesharecache:
			if o["content"] == item:
				found = True
		if not found:
			remotesharecache.append({"dt": datetime.datetime.utcnow().isoformat(), "content":item})
	

	def fetch_stream(self, privatekey, remotesharecache, remotestream, remoteid=""):
		""" Fetch shared items from a remote stream, and update remote share cache with them"""
		(remoteprofile, remoteshares) = self.load_and_check_publicstream(remotestream)
		if remoteprofile != False: #Has it loaded correctly (signed correctly, etc)
			if remoteid=="" or remoteid == remoteprofile["id"]: #Check if remote profile id matches stored ID (=key hash) to confirm continued identity
				#TODO Update profile; alt-urls -> in followlist, sharelist
				for share in remoteshares: #go through each share to see whether we can read it
					content1 = None
					try:
						#First, try to load public content
						content1 = json.loads(share)
					except:
						# decrypt the share with our private key
						unencshare = rsa.decrypt(str(share), privatekey) #Try whether we can
						try:
							#remember, we have three iterations of json-as-string-in-json here!
							content1 = json.loads(unencshare)
						except ValueError, e:
							logging.debug("Obviously a share is not meant for us...:")
							logging.debug(e)
					if content1 != None:
						content2m = hashlib.md5()
						content2m.update(content1["content"])
						chash = content2m.hexdigest()
						#check hash
						if chash == rsa.verify(str(content1["signature"]), json.loads(remoteprofile["pubkey"].decode("hex"))):
							content3 =json.loads(content1["content"])
							#update cache with found item
							self.addtoremotesharecache(remotesharecache, {"content":content3, "profile":remoteprofile})  #content3 is still un-de-jsoned
			else:
				logging.warning("Stored ID "+remoteid+" for "+remotestream+" does not match ID in remote file which is "+remoteprofile["id"])
		return remotesharecache

	def get_updates(self, privatekey, remotesharecache, followlist):
		""" check urls in your followlist for updates; add these updates to your remotesharecache and return
			the changed remotesharecache """
		for remote in followlist:
			remotesharecache = self.fetch_stream(privatekey, remotesharecache, remote["url"])
		return remotesharecache

	def output_updates_text(self, remotesharecache):
		""" Print the items in the remote share cache in text-only mode """

		#transform
		stream = {}
		for i in remotesharecache:
			stream[ i["dt"]+i["content"]["profile"]["id"] ] = i["content"]

		for key in sorted(stream.iterkeys()):
			print stream[key]["profile"]["name"]+" @ "+json.loads(stream[key]["content"]["content"])["datetime"]+" : "+json.loads(stream[key]["content"]["content"])["text"]

	def return_updates_as_array(self, remotesharecache):
		""" Print the items in the remote share cache in text-only mode """

		#transform
		stream = {}
		for i in remotesharecache:
			stream[ i["dt"]+i["content"]["profile"]["id"] ] = { "name": i["content"]["profile"]["name"], "date": json.loads(i["content"]["content"]["content"])["datetime"], "text": json.loads(i["content"]["content"]["content"])["text"] }

		return stream


if __name__ == "__main__":
	if DEBUG:
		logging.basicConfig(level=logging.DEBUG)

	profiledir = None
	optlist, args = getopt.getopt(sys.argv[1:], "d:", ["profiledirectory="])
	for o, a in optlist:
		if o in ("-d", "--profile-directory"):
			profiledir = a



	obj = Autonome(profiledir)

	if len(args) > 0:
		if args[0] == "create":
			if len(args) < 3:
				print "Format: create <Name> <Email>"
			else:
				obj.create_new_fileset(args[1], args[2], "", [])
		elif args[0] == "follow":
			if len(args) < 2:
				print "Format: follow <public-url>"
			else:
				privatekey = obj.load_private_key()
				(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
				followlist = obj.load_followlist(json.loads(myprofile["pubkey"].decode("hex")))
				followlist = obj.follow_stream(followlist, args[1])
				#always follow self
				followlist = obj.follow_stream(followlist, obj.get_config("Files", "PublicStream", None))
				obj.save_followlist(privatekey, followlist)
		elif args[0] == "unfollow":
			if len(args) < 2:
				print "Format: unfollow <public-url>"
			else:
				privatekey = obj.load_private_key()
				(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
				followlist = obj.load_followlist()
				followlist = obj.unfollow_stream(followlist, args[1])
				obj.save_followlist(privatekey, followlist)
		elif args[0] == "output-text":
			privatekey = obj.load_private_key()
			(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
			fn = obj.get_config("Files", "RemoteCache", obj.profiledir + os.sep + "RemoteCache")
			remotesharecache = obj.get_cachefile(fn, privatekey)
			followlist = obj.load_followlist(json.loads(myprofile["pubkey"].decode("hex")))
			remotesharecache = obj.get_updates(privatekey, remotesharecache, followlist)
			obj.output_updates_text(remotesharecache)
			obj.save_cachefile(fn, remotesharecache, json.loads(myprofile["pubkey"].decode("hex")))

		elif args[0] == "message-text":
			if len(args) < 3:
				print "Format: message-text <textmessage>  <tag1> [<tag2> [ <tag3> ... ]]"
				print "Use quotes!"
			else:
				privatekey = obj.load_private_key()
				(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
				sharelist = obj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
				fn = obj.get_config("Files", "LocalCache", obj.profiledir + os.sep + "LocalCache")
				
				sharecache = obj.get_cachefile(fn, privatekey)
				sharecache = obj.publish_text_message(privatekey, sharecache, myprofile, sharelist, args[1], args[2:])
				obj.save_cachefile(fn, sharecache, json.loads(myprofile["pubkey"].decode("hex")))

		elif args[0] == "add-alt-url":
			if len(args) < 2:
				print "Format: add-alt-url <url>"
				print "Use quotes!"
			else:
				obj.privatekey = load_private_key()
				obj.add_alt_url(privatekey, args[1])
		elif args[0] == "remove-alt-url":
			if len(args) < 2:
				print "Format: remove-alt-url <url>"
				print "Use quotes!"
			else:
				obj.remove_alt_url(privatekey, args[1])
		elif args[0] == "share":
			if len(args) < 3:
				print "Format: share <profileurl> <tag1> [<tag2> [ <tag3> ... ]]"
			else:
				(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
				sharelist = obj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
				sharelist = obj.share_stream(sharelist, args[1], args[2:])
				privatekey = obj.load_private_key()
				obj.save_sharelist(privatekey, sharelist)
		elif args[0] == "unshare":
			if len(args) < 2:
				print "Format: unshare <public-url>"
			else:
				(myprofile, myshares) = obj.load_and_check_publicstream(obj.get_config("Files", "PublicStream", None))
				sharelist = obj.load_sharelist(json.loads(myprofile["pubkey"].decode("hex")))
				obj.unshare(sharelist,args[1])
				privatekey = obj.load_private_key()
				obj.save_sharelist(privatekey, sharelist)
	else:
		print """autono:me private social networking

Usage autonome.py [-d profile-directory] command
where command is one out of:

	create <name> <email>		- create a new profile
	follow <public-url>		- follow profile at <public-url>
	unfollow <public-ur>l		- no longer follow profile at 
					  <public-url>
	add_alt_url <url>		- publish profile location <url>
	remove_alt_url <url>		- remove profile location <url>
	unfollow <public-url>		- no longer follow profile at 
					  <public-url>
	share <public-url> <tag1> [ <tag2> ... ]
					- share with profile at <public-url>
					  whenever sharing something with 
					  <tag1> etc
	message-text <textmessage> <tag1> [ <tag2> ... ]
					- share a text message with <tag1> 
					  etc.
					  IMPORTANT: If you include the tag
					  'public' the message will be pub-
					  lished unencrypted.
	unshare <public-url>	 	- no longer share with profile at 
					  <public-url>
	output-text			- retrieve and display messages 
""" 

	obj.save_config()
