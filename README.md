### About the repo

This is an amateur coder's attempt to make it easier to find new music on Spotify, without using its algorithms. 

Essentially what I'm doing here is aggregating new music playlists from different publications and radio stations into a single playlist on Spotify.

Have written a blog post about why I coded this [here](http://shijith.com/blog/automating-music-discovery/).

### Who this is for

* Amateur coders who want to simplify how they go about finding new music
* Life hackers and others who want to automate aspects of their lives
* People who are unhappy with Spotify's algorithmic playlists like 'Release Radar' and 'Discover Weekly'

### What you'll find here

* A python script [update_script.py](update_script.py) that does most of the work
* A list of the spotify playlists i'm aggregating in [playlist_ids_full.csv](playlist_ids_full.csv)
* A file to place your spotify developer credentials in [cred_spotify.py](cred_spotify.py)
* A file to place your email credentials in [config_email.ini](config_email.ini) if you want be notified every week when the consolidated playlist is created
* A list of songs released recently in [master_list_online.csv](master_list_online.csv). When you aggregate songs, you'll be checking them against this list to see if they've been featured in lists earlier. To start with, it's populated with tracks from the playlists I'm aggregating.

### How to set it all up

1. Clone the repo with  
`git clone https://github.com/shijithpk/music-discovery.git`

2. Made extensive use of the spotipy [library](https://spotipy.readthedocs.io) to access the Spotify API. CD into the directory and install the modules you'll need with  
`pip install -r requirements.txt` 

3. **Create spotify credentials** -- You'll need to [set up](https://www.section.io/engineering-education/spotify-python-part-1/) a developer account at Spotify, if you don't have one already. Then put your client id, client secret and redirect url into [cred_spotify.py](cred_spotify.py).

4. **Create a new mail id** -- This is optional, but if you want to be notified by email every week when your playlist is ready, you'll need to create a new mail id to send those mails to yourself. This [page](https://realpython.com/python-send-email/) has detailed instructions on how to use gmail programatically to send emails. Then put in the email id where you want to receive the mail, the new email id you've created and its password into [config_email.ini](config_email.ini).

5. **Choose playlists to aggregate**
Open it in excel or libreoffice
HAVE A LIST OF PLAYLIST IDS WITH JUST PLAYLIST URLS 
SHOULD I HAVE AN AIRTABLE OF PLAYLISTS HERE? OR LISTS where a user can just tick what he wants and generate a playlist
SOME WAY FOR PEOPLE TO SELECT PLAYLISTS
START WITH A MINIMAL NUMBER OF PLAYLISTS SELECTED
This can work with any collection of playlists

Give instructions on how to update the playlist csv
Actually no, lt them figure out some things for themselves
just point them to a relevant link 
https://www.geeksforgeeks.org/how-to-append-a-new-row-to-an-existing-csv-file/


6. **Change the country code** -- You'll need to change one line in the script and put in the two-letter ISO code for your country. (Here's one [list](https://gist.github.com/frankkienl/a594807bf0dcd23fdb1b) of codes.) It's important for something called track [relinking](https://developer.spotify.com/documentation/general/guides/track-relinking-guide/). Essentially, if a track on a playlist isnt licensed for your country, Spotify will find a version of the track that's licensed. So you'll have fewer missing tracks.
        `spotify_market = 'IN'`


## How to use it
Once everything's set up, just run the script `python3 update_script.py`. Things should be done in half an hour, after which you'll find in your spotify, a playlist titled 'New Music for <your spotify user id>'. The playlist is set to private, but you can make it public if you want.

Note that the playlist gets wiped clean and new tracks get added every time you run the script (That is, if one of the playlists you're aggregating has been updated in the meantime.) But you can 'like' songs to add them to your liked songs list. There's [no limit](https://www.theverge.com/2020/5/26/21270409/spotify-song-library-limit-removed-music-downloads-playlists-feature) in Spotify to how many songs you can 'like'. You can decide later what you want to do with the tracks. For example, putting them in genre-wise playlists.

You can either run the script locally or on a virtual machine. (Schedule it to run every week using [cron](https://help.ubuntu.com/community/CronHowto)). I'm using a VM with Oracle Cloud's [free tier](https://www.oracle.com/in/cloud/free/), but you can use your cloud provide of choice like Google Cloud or  Amazon Web Services.

**Before uploading to a VM** -- If you do decide to run it from a remote machine, just make sure to run the script locally once and then move the directory remote. It helps in creating these 'access tokens' and 'refresh tokens' that are important for accessing the spotify api. You'll need to copy and paste an authorization code the first time, after which everything can be automated.

## Further customization

You can also modify the script in a way so that the previous week's playlist doesnt get wiped clean, and this weeks playlist tracks just gets added on top.
You'll have to modify the script accordingly. The code snippet
is 
sp.playlist_add_items('39s1hlg987JGqOeXkmuUUn', reversed(track_spotify_id_list), position=0)
there's also a limit of 10000 songs to a playlist, so when it gets close to that limit, you'll need to start adding songs to a new playlist or delete songs from the existing one and continue adding to it.
you can look at this script for an example for how id did it for one playlist
you can look at the script for an examle for how when the 10,000 limit is close, i create a new playlist and start adding to that

also upload your original script so that people can see what else i've done
    for example it has a warning that a plylist has gone stale, hasnt been updated in a while, and so it might be time to remove it

DONT GO INTO FULL DETAILS OF THE SCRIPT , JUST GO INTO THE PARTS WHERE PEOPLE MIGHT WANT TO DO SOME CUSTOMISATION

DOWNLOAD THE REPO AND SEE IF IT ACTUALLY WORKS FOR YOU, MINIMISE THE STEPS THAT PEOPL ACTUALLY HAVE TO DO 

IT'S GOOD TO GIVE A MASTER LIST OF SONGS THAT HAVE BEEN RELEASED
THEN AFTER THAT LET THEM BRANCH OFF ON THEIR OWN

in My cron , do a command for updating the github repo as well