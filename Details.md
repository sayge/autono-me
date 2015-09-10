# More #

Autono:me separates two tasks which other distributed social networks try to solve together: it separates the displaying and encoding of information from its distribution. autono:me only solves the first task and relies for the second task on untrusted web servers which can serve files. Autono:me creates a cryptographically secured file, which persons can put on any kind of file server on the web (personal web space, university web space, Dropbox, Ubuntu One, rapidshare, Freenet or I2P....). The only condition is that your contacts are somehow able to download this file. They can only read messages adressed to them, because these are the only messages they can decrypt. If anyone unauthorized downloads the file, no harm is done, because without the correct private key, nobody can read anything secret.

Because autono:me does not reinvent communication protocols between servers, it can rely on existing server solutions with minimal security risks. Additionally, because communication channels do not have to be trusted, it removes a whole number of security issues and allows even persons in countries without internet freedom to safely participate.

Its features are designed to make it especially suitable e.g. for being run on plug web servers, e. g. FreedomBoxes, on mobile phones and other such devices.

At the core of autono:me there is a small set of small software routines that modify a file which you make publicly available to others. In this file, your messages are protected with strong encryption such that only those people can access them whom you have authorized to do so. Even if one of your friends has their private keys stolen, attackers can only see what this friend can see. This file is additionally cryptographically signed such that it cannot be replaced by someone  who does not have access to your private key. It also has inbuilt support for backup urls in case your primary url is inaccessible or gets censored.

autono:me has no shiny graphical interface yet. At the moment there are two ways to run it:
  * a command line program.
  * a local server web server on your computer, serving a browser interface.

autono:me supports social networking without any central infrastructure, as the public file can be indexed by normal internet search engines; and contact urls can be made known and discovered the usual ways.

The software additionally supports aspects (e.g. "family", "work", "movielovers") and publishing news specifically to certain aspects and excluding others. It thus minimizes the danger of accidental disclosure of information to people not supposed to know about it.

The program additionally includes a set of routines that can be incorporated into other software that makes use of these networking features.

All these tools are free software under the GPL version 3.