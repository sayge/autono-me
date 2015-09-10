# Frequently  Asked Questions #

## What advantages does autono:me have? ##

  * instant data ownership for everybody
  * you can use it right now. no need to register anywhere.
  * easy to develop for, only a few hundred lines of Python
  * builds on the way the web works, by publishing and retrieving structured information over HTTP. No new communication protocols. Potentially compatible with lots of standards
  * can be used and scripted from the command line
  * fully decentralized. No central authority that could control anything. No federation of servers.
  * Free Software, as in freedom


## How is autono:me different from other decentralized social networking projects like Diaspora? Why create another social network? ##

First of all, autono:me basically is a protocol for sharing information at public URLs that is not tied to any particular software. In principle, there is no technical reason, Diaspora and autono:me could not be compatible - Diaspora (as well as Facebook or Appleseed or anyone else) could publish for each user a public stream file and pull in public stream files from external autono:me users.

That said, there are a couple of differences that are worth to notice that might help you decide whether autono:me has any value for you.

Here are some **advantages** of autono:me:

  * Diaspora (and nearly all other distributed networking projects) require you to run a server that is connected to the internet at all times. This enables real-time updates, but it might be too costly or too cumbersome for some users. autono:me does not run as server, and requires only a place for hosting files which is nowadays basically free.
  * If you use a multi-user server provided by someone else, some advantages of decentralization are lost, e.g. you have to trust the server operator that he or she does not spy on you. autono:me removes all reasons to do so.
  * internet-facing server software can be attacked from the internet, and especially new software can have security bugs, affecting your data and your privacy. autono:me relies for all internet communication only on untrusted HTTP servers. If you separate server and data manipulation physically, your security is heightened.
  * Because you manipulate your data on your local computer with your own copy of the software, you have total data ownership.
  * autono:me cannot have load problems or server downtime by default.
  * People in regions with active censorship who cannot access the internet freely can rely on persons who can take their data on physical mediums to other regions and post it there, even without having to trust these people (because all data is encrypted).

Here are some **disadvantages** of autono:me:

  * No real-time updates. No chat. Ever.
  * Using autono:me is more complicated than just registering at some public server administered by someone else. However, we are working on this.
  * Because you need to run the autono:me software to publish and to read, you cannot easily use autono:me from internet terminals or friends' computers. We are working on a portable USB stick version, though.
  * autono:me is by far not as advanced as Diaspora (no images, videos, Likes, and no file-sharing yet, but all these features are planned.)

The ideal case would be, if all free networking platforms also supported the autono:me file format, so that people could decide for themselves about the relative importance of convenience vs. privacy.

## How can autono:me help people in oppressive countries? ##

  * autono:me does not trust the network at all. Privacy and trust are not negotiated on protocol level, but on data level.
  * autono:me works even without direct internet access
  * autono:me has inbuilt support for hosting your data in multiple places, helping with firewalls that block popular servers
  * autono:me makes it hard to accidentally publish information to the wrong group of persons
  * autono:me allows its users to inspect and verify its source code, making deceptive backdoors impossible

## How can I help? ##

  * create an autono:me file and publish it on your homepage, directing people to use the software
  * if you know HTML, improve the templates for the web interface
  * if you know Python, help fix bugs and add features
  * If you run Mac OS X, we could use your help building packages, please contact us via email autonome@i2pmailorg.
  * coming soon: translations into other languages
  * Join the [Google group](http://groups.google.com/group/autonome-discuss/)
  * Please report bugs either here on the Issue Tracker or via the group
  * Other questions? Mail [autonome@i2pmail.org]  ([PGP / GPG Key](PGPKey.md))

## How secure is it? ##

  * At the moment, autono:me is still in pre-alpha stage and should not be used for any critical purposes.
  * That said, by default, autono:me uses a 1024-bit RSA key for signing and encryption. If you keep your private key safe, you should be fine.