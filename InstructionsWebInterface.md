# Setup and use autono:me via its web interface #


## Step 1: Download autono:me ##

Download a .zip (Windows) or .tar.gz (Linux) file from the "Download" Tab above and unpack it into a directory of your choice.

## Step 2: Start the web interface ##

  * Navigate to the folder where you have unpacked the files.
  * Start "webserver.exe" (Windows) or "webserver" (Linux)
  * A text-mode window should now pop up, informing you that the webserver has been started and showing you the location of your "profile directory". Please note this location, because it will be needed.

## Step 3: Set up an account with your web browser ##

  * Start your web browser (Firefox, IE and Chrome should work fine).
  * Enter into the address field: http://localhost:8082
  * You should now be greeted by a form, enabling you to enter your name and your email for account creation. You can but do not have to enter your real name. Name and email will not be validated.
  * After submitting, the web browser will take a very long time to load the next page. This is normal and should not be interrupted. The software performs very heavy cryptographic operations to create your files.

## Step 4: Finding your way around the web interface ##

The web interface has at the moment four parts:

  1. Your "wall". Here, the latest posts from your friends are displayed and you can post status updates yourself. You can decide whether status updates are public (readable for anyone on the internet). As soon as you start sharing with friends (see next feature), you will also be able to tick boxes for "aspects" with whom you can share specific updates. The wall must be refreshed manually at the moment and status updates from others will only appear after a while.
  1. Your "followlist": This list contains the URLs of public profiles you have subscribed to. You can enter any URL you like - as long as there are no profiles at this URL with either public updates or updates specifically shared with you, it will not make any difference.
  1. Your "sharelist": Here, you manage the URLs of friends who you want to share with and group friends into one or more "aspects".
  1. Your profile details.

If you want to try out following someone, you can follow the autono:me projects public feed which is available at
```
https://sites.google.com/site/autonomeproject/fe9e00007464c845e14219ebe380b803.publicstream?attredirects=0&d=1
```


## Step 5: Setting up a public URL for your profile ##

In order for your friends to subscribe to your updates on their computers, you need to publish your stream file. You can find the stream file in the profile directory which you have noted above, and you can publish it on the web any way you want.

Here are some instructions how to do it with Dropbox.

  1. Stop the server by clicking on "Stop Server" at the bottom of the page
  1. Navigate to the profile folder noted in Step 2.
  1. You will find in the "public" sub-folder a file with the file extension ".publicstream".
  1. Move that file to the "Public" folder inside your Dropbox folder.
  1. Go back to the profile directory
  1. Edit the file "settings.ini" with a text editor (Notepad on Windows).
  1. replace the entry "publicstreamfile=...." with the new location of your public stream file (full path, including drive letter on Windows).
  1. save the file
  1. go to the Public Dropbox folder again
  1. right-click the publicstream file; in the "Dropbox" sub-menu, choose "copy URL".
  1. This is now your profile URL. You can set it up in your profile information, as soon as you restart the web server. You can and should also share it with your friends. If you intend to post public updates, please consider also sharing it on our [Google Group](http://groups.google.com/group/autonome-discuss).


See also: [StartAutonomeAutomatically](StartAutonomeAutomatically.md)