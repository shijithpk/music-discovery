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

This is optional, but if you want to be notified by email every week when your playlist is ready, you'll need to create a new gmail account to send those mails to yourself. This [page](https://realpython.com/python-send-email/) has pretty detailed instructions. Then put in the email id where you want to receive the mail, the new email id you've created and its password into config_email.ini.

HAVE A LIST OF PLAYLIST IDS WITH JUST PLAYLIST URLS 

HAVE SEPARATE NEW MUSIC UPDATE PY FOR GITHUB

DOWNLOAD THE REPO AND SEE IF IT ACTUALLY WORKS FOR YOU, MINIMISE THE STEPS THAT PEOPL ACTUALLY HAVE TO DO 
SELECT PLAYLISTS

SHOULD I SORT BY POPULARITY FOR THE SONGS

IT'S GOOD TO GIVE A MASTER LIST OF SONGS THAT HAVE BEEN RELEASED
THEN AFTER THAT LET THEM BRANCH OFF ON THEIR OWN

START WITH A MINIMAL NUMBER OF PLAYLISTS SELECTED

DO A REGEX SO THAT YOU CAN EXTRACT ID FROM PLAYLIST URL
MAKE THINGS AS EASY FOR POEPLE AS POSSIBLE

MAKE A PLAYLIST WITH A DEFAULT NAME , include their spotify username, something like New Music Playlist for XXXXXusernameXXXX

in My cron , do a command for updating the github repo as well

also upload your original script so that people can see what else i've done
    for example warning that a plylist has gone stale, hasnt been updated in a while, and so it might be time to remove it


look in your spotify playlists for a playlist titled 'New Music for <your spotify user id>'. It's set to private, but you can make it public if you want.

might be easier to create your own project than following someone else's code. GO for it, i won't mind.

sp.current_user()
{'display_name': 'Shijith Kunhitty', 'external_urls': {'spotify': 'https://open.spotify.com/user/shijith'}, 'followers': {'href': None, 'total': 3}, 'href': 'https://api.spotify.com/v1/users/shijith', 'id': 'shijith', 'images': [{'height': None, 'url': 'https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=10152024542046837&height=300&width=300&ext=1626154084&hash=AeQn7jeLjpCxMGGWpS4', 'width': None}], 'type': 'user', 'uri': 'spotify:user:shijith'}


PUT IN SOME OF SPOTIFY's OWN CURATED PLAYLISTS INTO THE LIST, NO ACTUALLY DONT


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

STOP USING THE WORD CONSTITUENT SO MUCH

DONT GO INTO FULL DETAILS OF THE SCRIPT , JUST GO INTO THE PARTS WHERE PEOPLE MIGHT WANT TO DO SOME CUSTOMISATION

### Where to host the script
I'm using Oracle Cloud's [free tier](https://www.oracle.com/in/cloud/free/), which offers two virtual machines for free forever. But you can use your cloud provider of choice--Google Cloud, Amazon Web Services etc.

### Scheduling the script DO WE NEED THIS?
mention cron








