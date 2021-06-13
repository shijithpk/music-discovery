# WRITE THIS MORE ANALYTICALLY, HINDU SMART

### About the repo

This is an amateur python coder's attempt to make it easier to find new music on Spotify, without using its algorithms. 

Essentially what I'm doing here is aggregating new music playlists from different publications and radio stations into a single playlist.

Have written a blog post about why I coded this [here](http://shijith.com).


### Who this is for

* Amateur coders like myself who want to simplify how they find new music
* Life hackers and others who want to automate aspects of their lives
* People who are unhappy with Spotify's algorithmic playlists like 'Release Radar' and 'Discover Weekly'

# GIVE LINKS TO FILES BELOW???

### What you'll find here

* A python script new_music_update.py that does most of the work
* A list of the playlists i'm aggregating in playlist_ids.csv
* A file to place your spotify developer credentials in cred_SAMPLE.py
* A file to place your email credentials if you want be notified every week when the consolidated playlist is created
* A list that has all the songs you've ever added to the consolidated playlist in master_list_online.csv. So if a song has been added to the consolidated playlist in the past, it won't get added again.
* A list that has all the songs added to all the constituent playlists every week in master_list.csv . Has its uses.

IF YOU'RE GOING TO CREATE THE MASTERLISTS FRESH, DO YOU NEED TO UPLOAD IT TO THE REPO? ISNT JUST GIVING A FLIMPSE OF IT ENOUGH?

SHOULD I HAVE AN AIRTABLE OF PLAYLISTS HERE? OR LISTS where a user can just tick what he wants and generate a playlist

### Getting started

Clone the repo with  
`git clone https://github.com/shijithpk/music-discovery.git`

Made extensive use of the spotipy [library](https://spotipy.readthedocs.io) to access the Spotify API. CD into the directory and install the modules you'll need with  
`pip install -r requirements.txt` 

You'll need to [set up](https://www.section.io/engineering-education/spotify-python-part-1/) a developer account at Spotify, if you don't have one already. Put in your client id, client secret and redirect url into cred_RENAME.py. Rename the file to cred.py for it to work.

This is optional, but if you want to be notified by email every week when your playlist is ready, you'll need to create a new gmail account to send those mails to yourself. This [page](https://realpython.com/python-send-email/) has pretty detailed instructions. Then put in the email id where you want to receive the mail, the new email id you've created and its password into config_RENAME.ini. Rename it to config.ini for it to work.

have a list of playlist ids with just playlist urls 

have separate new music update py for github

download the repo and see if it actually works for you, minimise the steps that peopl actually have to do 
select playlists



### More about the script


### First time running the script



check if csv is not there 

and if not there , generate it

This can work with any collection of playlists


### Before uploading to the VM

How Spotify, you'll need to run it once locally and then 

Setting up your script in a way so that it can run on its own is made a bit 
[](https://www.codeproject.com/Tips/5276627/HowTo-Setup-a-Spotify-API-App-in-the-Spotify-Devel)

"scope": "playlist-read-private playlist-modify-private playlist-modify-public"

GO INTO SOME DETAILS OF  THE SCRIPT ETC. THEN GO INTO THE NITTY-GRITTY

THIS SCRIPT HOSTING BIT SHOULD BE AT THE END, AFTER EVERYTHING ELSE

### Where to host the script
I'm using Oracle Cloud's [free tier](https://www.oracle.com/in/cloud/free/), which offers two virtual machines for free forever. But you can use your cloud provider of choice--Google Cloud, Amazon Web Services etc.

### Scheduling the script DO WE NEED THIS?
mention cron








