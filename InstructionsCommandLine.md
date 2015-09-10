# Setting up and running autono:me via the command line #

autono:me works the following way: You have one very important file which is called your "public stream" (called something.publicstream). This file contains, encrypted and signed information. You publish this file at any URL (your Dropbox or Ubuntu One account, your web page, wherever...). Your friends then can subscribe to this file and, provided you share things with them, read your posts.

autono.me creates also some other files, most importantly a file where is stores your configuration (settings.ini) and your private key (something.privatekey). You should keep your private key secret.

These files are by default in the following directory:
  * under Linux: /home/yourusername/.local/share/autonome
  * under Windows: TBC
  * under Mac OS: TBC


# Create a profile #

Creating a profile via the command line is easy:

Navigate to the folder where you have unpacked the downloaded archive.
Run:
```
./autonome create <your name> <your email address> 
```
If you want your name to have spaces in it, please enclose it in double quotes.
So for example:
```
./autonome create "James Bond" jamesbond007@mi5.gov.uk
```

# Publish your public stream file #

If you have not used any special options, your public stream file will be in the folder noted above. You can now go to this folder and upload it to some web server.

If you use Dropbox or a similar service, you can also do the following:
  * Go to your profile folder (see above)
  * move the file "....publicstream" which is located in the "public" sub-folder into your Dropbox public folder (or the equivalent)
  * open the file "settings.ini" in a text editor
  * In the section [Files](Files.md), edit the line "publicstream=....." so that it points to the new location of the public stream file.

You can now publish the URL of your stream file, so that your friends can follow you.

If you intend to post public updates, please consider also sharing it on our [Google Group](http://groups.google.com/group/autonome-discuss).

# Subscribe to other people's streams #

If you want to follow someone's stream, just enter
```
./autonome follow <url>
```

**Note**: As long as the other person has not shared some posts privately with you, you can only see their public posts.

If you want to try out following someone, you can follow the autono:me projects public feed which is available at
```
https://sites.google.com/site/autonomeproject/fe9e00007464c845e14219ebe380b803.publicstream?attredirects=0&d=1
```

# Setting up sharing #

Let's you want to share in the future some posts with your friend who has a public stream at http://example.com/example.publicstream.

In autono:me sharing, **aspects** play a major role. Always when you post something, you post it to certain aspects which represent some groups of your friends (e.g. family, friends, operalovers, and so on). Each friend can be in one or several aspects.

In order to set up autono:me such that it shares all your future posts to the "friends" and to the "operalovers" aspect with the above described friend, enter:
```
./autonome share http://example.com/example.publicstream family friends
```

# Posting a status update #

Having set up your profile now in this way, you might want to post a status update, let's say one which is visible only to your friends:

```
./autonome message-text "I'm now on autono:me!!!!" friends
```

or

```
./autonome message-text "La Traviata last night in the met was awesome" operalovers friends
```

You can also share posts with everyone who might subscribe to your stream by adding the special aspect "public":

```
./autonome message-text "A public post" public
```

As you can see, it is very easy to automate this with cron scripts, to automatically publish the output of programs and so on.

If your public stream does not get published automatically, do not forget to publish the modified file after posting.

# Fetching and displaying updates from your friends #

Of course, having subscribed now to a few friends, you will regularly want to see if they have posted something.
```
./autonome output-text
```

By default, autono:me checks each particular stream only every 30 minutes, so running the script more often neither helps nor hurts.