### About the repo

This is an amateur coder's attempt to make it easier to find new music on Spotify without using its algorithms. 

Essentially what I'm doing here is aggregating new music playlists from different publications and radio stations into a single playlist on Spotify.

Have written a blog post about why I coded this [here](http://shijith.com/blog/automating-music-discovery/).

### Who this is for

* Amateur coders who want to spend less time  finding new music
* Life hackers and others who want to automate aspects of their lives
* People unhappy with Spotify's algorithmic playlists like 'Release Radar' and 'Discover Weekly'

### What you'll find here

* [update_script.py](update_script.py) that does most of the work. 
* [playlist_ids_full.csv](playlist_ids_full.csv) which has a list of Spotify playlists you can aggregate 
* [cred_spotify.py](cred_spotify.py) where you'll place your Spotify developer credentials 
* [config_email.ini](config_email.ini) where you'll place your email credentials, if you want be notified every week when the consolidated playlist is created
* [master_list_online.csv](master_list_online.csv), which is a list of songs released recently. When the script comes across a song, it will check the song against this list to see if it's been on playlists earlier. The csv's been populated with songs from playlists I'm aggregating.
* [further_ideas_1.py](further_ideas_1.py) and [further_ideas_2.py](further_ideas_2.py) for inspiration on how to customize update_script.py  

### How to set it all up

1. Clone the repo with `git clone https://github.com/shijithpk/music-discovery.git`

2. CD into the directory and install the modules you'll need with `pip install -r requirements.txt`. I've made extensive use of the spotipy [library](https://spotipy.readthedocs.io) to access the Spotify API.

3. **Create Spotify credentials** — You'll need to [set up](https://www.section.io/engineering-education/spotify-python-part-1/) a developer account at Spotify, if you don't have one already. Then put your client id, client secret and redirect url into [cred_spotify.py](cred_spotify.py).

4. **Create a new mail id** — This is optional, but if you want to be notified by email every week when your playlist is ready, you'll need to create a new mail id to send those mails to yourself. This [page](https://realpython.com/python-send-email/) has detailed instructions on how to use gmail programatically to send emails. Then put in the email id where you want to receive the mail, the new email id you've created and its password into [config_email.ini](config_email.ini). (And if you decide against email notifications, go into [update_script.py](update_script.py) and delete the part dealing with email.)

5. **Choose playlists to aggregate** — [playlist_ids_full.csv](playlist_ids_full.csv) has a list of Spotify playlists you can aggregate. Info on each playlist is available like its source and genre. If you think you want to include a playlist, just put 'yes' against it in the INCLUDE column. And if you don't want to include it, just leave the cell under INCLUDE blank.

6. **Change the country code** — You'll need to change one line in the script `spotify_market = 'IN'` and put in the two-letter ISO code for your country. (You can find the code from this [list](https://gist.github.com/frankkienl/a594807bf0dcd23fdb1b).) It's important for something called track [relinking](https://developer.spotify.com/documentation/general/guides/track-relinking-guide/). Essentially, if a track on a playlist isn't licensed for your country, Spotify will find a version of the track that is licensed, so you'll have fewer tracks missing.  

### How to use it
Once everything's set up, just run the script `python3 update_script.py`. Things should be done in half an hour, after which you'll find in your Spotify libary a playlist titled 'New Music for \< your Spotify user id \>'. The playlist is set to private, but you can make it public if you want.

Note that the playlist gets wiped clean and new tracks get added every time you run the script (as long as one of the playlists you're aggregating has been updated in the meantime.) I've never gotten more than 160 songs in an update and that may sound like a lot, but it's easy to get through those songs in a week.

It doesn't have to be a chore, just have the playlist running while you're working/browsing/doomscrolling and 'like' songs to add them to your liked songs list. There's [no limit](https://www.theverge.com/2020/5/26/21270409/spotify-song-library-limit-removed-music-downloads-playlists-feature) in Spotify to how many songs you can 'like'. You can decide later what you want to do with the songs you've liked. (For example, you can put them in genre-wise playlists if you want.)

You can either run the script locally or on a virtual machine (VM). (Schedule it to run every week using [cron](https://help.ubuntu.com/community/CronHowto)). I'm using a VM with Oracle Cloud's [free tier](https://www.oracle.com/in/cloud/free/), but you can use your cloud provider of choice like Google Cloud or Amazon Web Services. [This](https://docs.oracle.com/en/learn/cloud_free_tier/index.html#introduction) and [this](https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/flask-on-ubuntu/01oci-ubuntu-flask-summary.htm) will help you get started with Oracle Cloud's free tier.

+ **Before uploading to a VM** — If you do decide to run it from a remote machine, just make sure to run the script locally once and then move the whole directory remote. A local run creates these 'access tokens' and 'refresh tokens' in a hidden .cache file that are important for accessing the Spotify API. You'll have to copy and paste an authorization code manually the first time you use your credentials, but after that everything can be automated.

### Further customization

(This section won't have much handholding. You'll have to get your hands dirty and figure things out on your own here!)

* **Add new playlists** — You can also add other Spotify playlists to [playlist_ids_full.csv](playlist_ids_full.csv). First get the playlist_url from Share > 'Copy Link To Playlist' on the playlist's page. This [guide](https://www.geeksforgeeks.org/how-to-append-a-new-row-to-an-existing-csv-file/) will show you how to add new rows to a csv. (Use the 2nd method where you append dictionaries as new rows. Has more typing, but it's clearer.) When adding a new row, the only values that are required are playlist_url and a 'yes' value in the INCLUDE column. The other values are optional, but it's nice to have that info so you know what each playlist is about.

* **Retain previous weeks' tracks** — Right now the updates are done in such a way that tracks added last week are removed, and fresh tracks come in its place. But you can also modify the script to ensure the previous week's playlist isn't wiped clean, and new tracks from this week just get added to the top of the playlist. [further_ideas_1.py](further_ideas_1.py) will show you how to implement this.  

* **Deal with the 10,000 song-limit** — If you decide to retain songs from previous weeks, one issue that you will bump up against is the limit of 10,000 songs for a Spotify playlist. How [further_ideas_1.py](further_ideas_1.py) gets over it is by deleting the oldest songs as soon as the song-count nears 10,000. Instead of deleting older tracks, another thing you could do is create a new playlist and add songs to that. [further_ideas_2.py](further_ideas_2.py) will show you how to automate the process. 

* **Find out which playlists are inactive** — Some of the playlists you're aggregating, they might stop getting updates after a while, but you can use email to monitor how active different playlists are. [further_ideas_2.py](further_ideas_2.py) implements this by mailing me with info about each playlist's last update (screenshot below).

![Screenshot of email](https://i.imgur.com/ttPLsUP.png)

### Suggestions, criticism etc.
I'm not a professional coder/developer/programmer, so am sure there are things here I should be doing differently. If you have any suggestions, please contact me on mail@shijith.com or at my twitter handle [@shijith](https://twitter.com/shijith).  

For example, I'd be especially interested in hearing if I should store the tracks and their details in a database instead of a CSV. Thought it would be overkill for a small project like this, but was thinking that in a few years from now, the CSVs might get too large to do all the analysis in memory and might slow everything down. Let me know! :)