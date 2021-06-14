### About the repo

This is an amateur python coder's attempt to make it easier to find new music on Spotify, without using its algorithms. 

Essentially what I'm doing here is aggregating new music playlists from different publications and radio stations into a single playlist on Spotify.

Have written a blog post about why I coded this [here](http://shijith.com).

### Who this is for

* Amateur coders like myself who want to simplify their process of finding new music
* Life hackers and others who want to automate aspects of their lives
* People who are unhappy with Spotify's algorithmic playlists like 'Release Radar' and 'Discover Weekly'

### What you'll find here

* A python script [update_script.py](update_script.py) that does most of the work
* A list of the spotify playlists i'm aggregating in playlist_ids_4github.csv
* A file to place your spotify developer credentials in cred_SAMPLE.py
* A file to place your email credentials if you want be notified every week when the consolidated playlist is created
* A list that has all the songs you've ever added to the consolidated playlist in master_list_online.csv. So if a song has been added to the consolidated playlist in the past, it won't get added again.
* A list that has all the songs added to all the constituent playlists every week in master_list.csv . Has its uses.


### Getting started

Clone the repo with  
`git clone https://github.com/shijithpk/music-discovery.git`

Made extensive use of the spotipy [library](https://spotipy.readthedocs.io) to access the Spotify API. CD into the directory and install the modules you'll need with  
`pip install -r requirements.txt` 

You'll need to [set up](https://www.section.io/engineering-education/spotify-python-part-1/) a developer account at Spotify, if you don't have one already. Put in your client id, client secret and redirect url into cred_RENAME.py. Rename the file to cred.py for it to work.

This is optional, but if you want to be notified by email every week when your playlist is ready, you'll need to create a new gmail account to send those mails to yourself. This [page](https://realpython.com/python-send-email/) has pretty detailed instructions. Then put in the email id where you want to receive the mail, the new email id you've created and its password into config_email.ini.

HAVE A LIST OF PLAYLIST IDS WITH JUST PLAYLIST URLS 

SHOULD I HAVE AN AIRTABLE OF PLAYLISTS HERE? OR LISTS where a user can just tick what he wants and generate a playlist

DOWNLOAD THE REPO AND SEE IF IT ACTUALLY WORKS FOR YOU, MINIMISE THE STEPS THAT PEOPL ACTUALLY HAVE TO DO 
SELECT PLAYLISTS

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

Give instructions on how to update the playlist csv
Actually no, lt them figure out some things for themselves
just point them to a relevant link 
https://www.geeksforgeeks.org/how-to-append-a-new-row-to-an-existing-csv-file/

the playlist will get wiped clean every week, you can just like songs and it will be there in your liked songs list, you can decide what you want to do with them later, put them in separate playlists etc.
You can also modify the script in a way so that the previous week's playlist doesnt get wiped clean, and this weeks playlist tracks just gets added on top.
You'll have to modify the script accordingly. The code snippet
is 
sp.playlist_add_items('39s1hlg987JGqOeXkmuUUn', reversed(track_spotify_id_list), position=0)
there's also a limit of 10000 songs to a playlist, so when it gets close to that limit, you'll need to start adding songs to a new playlist or delete songs from the existing one and continue adding to it.
you can look at this script for an example for how id did it for one playlist
you can look at the script for an examle for how when the 10,000 limit is close, i create a new playlist and start adding to that

should i create a github page of awesome list of spotify new music playlists?

also change the country code


YOU SHOULDNT GO TOO DEEP INTO HANDHOLDING

### Where to host the script
I'm using Oracle Cloud's [free tier](https://www.oracle.com/in/cloud/free/), which offers two virtual machines for free forever. But you can use your cloud provider of choice--Google Cloud, Amazon Web Services etc.

### Scheduling the script DO WE NEED THIS?
mention cron








