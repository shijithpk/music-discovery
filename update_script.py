#!/home/ubuntu/py313/bin/python

from datetime import datetime
from datetime import timedelta
from thefuzz import fuzz,process
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred_spotify
import math
import os
import pandas as pd
import time
import re
import unidecode

scope = "playlist-read-private playlist-modify-private playlist-modify-public playlist-modify-public"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred_spotify.client_id , client_secret= cred_spotify.client_secret ,redirect_uri=cred_spotify.redirect_url, scope=scope, open_browser=False))

#you'll need to change the line below and put in the code for your country
	# here's one list of codes -- https://gist.github.com/frankkienl/a594807bf0dcd23fdb1b
	# something about it enabling track relinking. Essentially, if a version of a track isnt licensed 
		#for your country, spotify gets you a version that is licensed. 
		# More info at https://developer.spotify.com/documentation/general/guides/track-relinking-guide/
spotify_market = 'IN'

# getting current user's id
current_user_object = sp.current_user()
current_user_id = current_user_object['id']

# name of the new music playlist
	#this is where the consolidated music will appear
	#you can modify it however you want
playlist_title_to_update = 'New Music for ' + current_user_id

#Check if a playlist is there by this playlist_title
	#if it is there, get the playlist id
	#if not create the playlist and then get its id

# this code block gets a list of names of the user's public and private playlists
resultsy = sp.current_user_playlists(limit=50,offset=0)
items = resultsy['items']
while resultsy['next']:
	time.sleep(5)
	resultsy = sp.next(resultsy)
	items.extend(resultsy['items'])
name_id_dict = {}
for item in items:
	playlist_name = item['name']
	playlist_id = item['id']
	name_id_dict[playlist_name] = playlist_id
playlist_name_list = list(name_id_dict.keys())

if playlist_title_to_update in playlist_name_list:
	playlist_id_to_update = name_id_dict[playlist_title_to_update]
else:
	new_playlist_object = sp.user_playlist_create(current_user_id, 
								playlist_title_to_update, 
								public=False, 
								collaborative=False, 
								description='Songs compiled from new music lists of various publications, websites and radio stations')
	playlist_id_to_update = new_playlist_object["id"]

now = datetime.now()
current_year = str(now.year)

playlist_ids_df = pd.read_csv('playlist_ids_full.csv')
master_list_online_df = pd.read_csv('master_list_online.csv')

one_year_ago = now - timedelta(days=365)
master_list_online_df['date_released'] = pd.to_datetime(master_list_online_df['date_released'], errors='coerce')
master_list_online_df = master_list_online_df[master_list_online_df['date_released'] >= one_year_ago]

#this master_list_online_df is the list we will check for duplicates against


# ---------------------------------------------------------------------------
# Helper functions
#
# These are small utilities used further down. They're defined up here so the
# main part of the script below reads top-to-bottom without interruption.
# ---------------------------------------------------------------------------

def normalize_for_cache(text):
	#Turn a song's 'name + artist' string into a simplified lookup key.
		#We strip accents (so 'Beyoncé' matches 'Beyonce'), remove punctuation,
		#lowercase everything and squeeze repeated spaces into one. Two songs
		#that produce the same key are treated as the same song.
	normalized = unidecode.unidecode(text or '')
	normalized = re.sub(r'[^\w\s]', '', normalized)
	return ' '.join(normalized.lower().split())

# The snapshot cache lets us skip playlists that haven't changed since the last run.
	#Spotify gives every playlist a 'snapshot_id' that changes whenever the playlist's
	#contents change. We store each playlist's snapshot_id in a small CSV. On the next
	#run, if a playlist's snapshot_id matches what we saved, nothing's changed, so we
	#can skip downloading and checking all its songs.
		#(It's safe to skip, because any song worth adding would already be in
		#master_list_online.csv from an earlier run, so it'd be treated as a
		#duplicate now anyway.)
	#This is optional - if you'd rather keep things simple, you can delete the
	#snapshot bits and the script will just check every playlist every time.
SNAPSHOT_CACHE_PATH = 'playlist_snapshot_cache.csv'

def load_playlist_snapshot_cache(path):
	#Read the snapshot cache CSV into a {playlist_id: snapshot_id} dictionary.
		#If the file doesn't exist yet (eg. on your very first run), return an
		#empty dict so that every playlist gets processed.
	if not os.path.exists(path):
		return {}

	snapshot_df = pd.read_csv(path, dtype=str).fillna('')
	if 'playlist_id' not in snapshot_df.columns or 'snapshot_id' not in snapshot_df.columns:
		return {}

	return dict(zip(snapshot_df['playlist_id'], snapshot_df['snapshot_id']))

def save_playlist_snapshot_cache(rows, path):
	#Write the snapshot_ids collected this run back to the cache CSV.
		#We write to a temporary file first and then rename it, so that an
		#interrupted run can't leave behind a half-written cache file.
	snapshot_df = pd.DataFrame(rows, columns=['playlist_id', 'snapshot_id', 'last_seen'])
	tmp_path = f"{path}.tmp"
	snapshot_df.to_csv(tmp_path, index=False)
	os.replace(tmp_path, path)

def fetch_playlist_snapshot_id(sp, playlist_id):
	#Ask Spotify for just this playlist's snapshot_id (a lightweight call).
		#If the call fails for any reason, return an empty string so that the
		#playlist gets processed normally rather than skipped by mistake.
	try:
		result = sp.playlist(playlist_id, fields='snapshot_id')
		return result.get('snapshot_id', '')
	except Exception as e:
		print(f"Could not fetch snapshot_id for playlist {playlist_id}; processing it normally. Reason: {e}")
		return ''


#creating a dataframe that we will be merging with the master list online dataframe later on
column_names_online = ['track_id', 'track_name', 'artist_name', 'artist_id', 'date_released',
	   'date_added_to_online_list', 'danceability', 'energy', 'key',
	   'loudness', 'speechiness', 'acousticness', 'instrumentalness',
	   'liveness', 'valence', 'tempo', 'duration_ms', 'combined_string']

# Instead of adding songs to a dataframe one row at a time (which gets slow as the
	#dataframe grows), we collect each new song as a dictionary in this list and
	#build the dataframe in one go after the loop.
online_rows = []

# We'll also collect each processed playlist's snapshot_id here, to save to the
	#cache file at the end of the run.
current_snapshot_rows = []

# To check whether a song is a duplicate, we compare it against the songs already in
	#master_list_online.csv. We pull out the bits we need once, up front, so we're not
	#rebuilding these lookups for every single song inside the loop.
		#- existing_online_track_ids: the Spotify track ids we've seen before
		#- existing_online_combined_strings: the raw 'name + artist' strings, for fuzzy matching
		#- existing_online_combined_keys: the normalized keys, for fast exact-duplicate checks
existing_online_track_ids = set(master_list_online_df['track_id'].dropna())
existing_online_combined_strings = master_list_online_df['combined_string'].dropna().tolist()
existing_online_combined_keys = set()
for value in existing_online_combined_strings:
	combined_key = normalize_for_cache(value)
	if combined_key:
		existing_online_combined_keys.add(combined_key)

# These keep track of the songs we've already added during THIS run, so that the
	#same song turning up on two different playlists this week doesn't get added twice.
this_week_online_track_ids = set()
this_week_online_combined_strings = []
this_week_online_combined_keys = set()

# Load the snapshot cache saved by the previous run (an empty dict on the first run).
playlist_snapshot_cache = load_playlist_snapshot_cache(SNAPSHOT_CACHE_PATH)

#here we are looping over the playlists, taking them one by one
for index,row in playlist_ids_df.iterrows():
	playlist_url = row['playlist_url']
	regex_pattern = r'.+playlist\/(.+?(?=\?|$))'
	playlist_id = re.match(regex_pattern, playlist_url).group(1)
	#so this regex will get the playlist id from both
		#urls like this https://open.spotify.com/playlist/5359l8Co8qztllR0Mxk4Zv?si=bb87bb1789b240e7
			#and like this https://open.spotify.com/playlist/5359l8Co8qztllR0Mxk4Zv
	include_boolean = row['INCLUDE']

	#Option to follow the playlist you've chosen on Spotify
	#have commented it out because every playlist you follow
		#will appear in your spotify library and I didnt 
		#want to clutter your Spotify library with 20-30 
		#playlists at one go. What I do is I follow the 
		#new music playlists so that it helps their 
		#follower count, but I put them in a separate folder
		#so that my library doesnt look cluttered

	#UNCOMMENT BLOCK BELOW IF YOU WANT TO GIVE THE PLAYLISTS YOU CHOOSE A FOLLOW
	# if not sp.playlist_is_following(playlist_id,
	#                                 [current_user_id])[0]:
	#     sp.current_user_follow_playlist(playlist_id)

	if ((include_boolean == 'yes') or (include_boolean == 'Yes') or (include_boolean == 'YES')):

		#first check the playlist's snapshot_id. If it's the same as last run, the
			#playlist hasn't changed, so we just record its snapshot and skip it.
		snapshot_id = fetch_playlist_snapshot_id(sp, playlist_id)
		time.sleep(5)
		if snapshot_id and playlist_snapshot_cache.get(playlist_id) == snapshot_id:
			current_snapshot_rows.append({
				'playlist_id': playlist_id,
				'snapshot_id': snapshot_id,
				'last_seen': datetime.today().strftime('%Y-%m-%d'),
			})
			continue

		# here we are getting all the tracks of a constitutent playlist
		results = sp.playlist_items(playlist_id, offset=0, market=spotify_market)
		items = results['items']
		while results['next']:
			time.sleep(6)
			results = sp.next(results)
			items.extend(results['items'])

		#now we look at each song/track in a playlist
			#whether it was released this year, whether it's been added to the playlist in the past etc.
		for item in items:
			if item['track']:
				episode_boolean = item['track']['episode']
				# it's like this in api output, "episode": false
				#if boolean is true, skip this item in loop and move to next item
				if episode_boolean:
					continue
				track_name = item['track']['name']
				track_id = item['track']['id']
				artist_name_list = [artist['name'] for artist in item['track']['artists']]
				#some tracks (eg. local files) can have a missing artist name; skip those
					#so the ', '.join below doesn't error out
				if None in artist_name_list:
					continue
				artist_name = ', '.join(artist_name_list)
				combined_string = track_name + ' ' + artist_name
				artist_id_list = [artist['id'] for artist in item['track']['artists']]
				artist_id = ', '.join(artist_id_list)
				album_name = item['track']['album']['name']
				album_id = item['track']['album']['id']
				date_released = item['track']['album']['release_date']
				#some tracks can have a missing release date; skip those so the
					#len() check below doesn't error out
				if not date_released:
					continue
				date_added_to_playlist = item['added_at'][0:10]
				date_added_to_master_list = datetime.today().strftime('%Y-%m-%d')
				
				# here we are looking at the release date of a song 
				#this is to make sure we get only songs released this year or in the last two months
				# Lots of old songs just have a year in release date, need a check to see if date released string length is 10 characters
					#10 characters being the length of a 'YYYY-MM-DD' string, including the hyphens between the numbers
				if len(date_released) == 10:
					date_released_object = datetime.strptime(date_released, '%Y-%m-%d')
					days_since_release = now - date_released_object

					#if released this year or in last two months
						#last two months check allows for songs released in Nov/Dec to appear in playlist in Jan/Feb
					if (current_year in date_released) or (days_since_release < timedelta(weeks = 9)):

						#below we check if it's not a duplicate of a track that we've added in the past
							#We do this by checking against existing track ids in the master list , 
								# also by checking whether another playlist this week has the same track id
								# also by doing fuzzy matches. If it's a score less than 100, we can add it
									# Am ok with duplicates being added to the list, not ok with missing out on tracks

						#the normalized key for this song, used for the fast exact-duplicate checks below
						combined_key = normalize_for_cache(combined_string)

						#skip if we've already got this exact track id - either from a
							#previous run (it's in the master list) or earlier this run
						if track_id in existing_online_track_ids:
							continue
						if track_id in this_week_online_track_ids:
							continue

						#skip if a different track id has the same normalized name+artist
							#(catches re-releases / different versions of the same song,
							#including accented spellings like 'Beyoncé' vs 'Beyonce')
						if combined_key in existing_online_combined_keys:
							continue
						if combined_key in this_week_online_combined_keys:
							continue

						#finally a fuzzy check, to catch near-matches the exact checks miss
							#(eg. the same words in a different order). A score of 100 means
							#it's effectively the same song, so we skip it.
						if this_week_online_combined_strings:
							match_this_week = process.extractOne(combined_string, this_week_online_combined_strings, scorer=fuzz.token_set_ratio)
							chance_of_match_in_this_weeks_other_tracks = match_this_week[1] if match_this_week else 0
						else:
							chance_of_match_in_this_weeks_other_tracks = 0

						if chance_of_match_in_this_weeks_other_tracks >= 100:
							continue

						match_existing = process.extractOne(combined_string, existing_online_combined_strings, scorer=fuzz.token_set_ratio)
						chance_of_match_in_existing_playlist_tracks = match_existing[1] if match_existing else 0

						if chance_of_match_in_existing_playlist_tracks >= 100:
							continue

						#if we've got this far, there's no track with a different id that is a fuzzy match of the track we are looking at, so we can add it

						# Oct 12, 2025 note: spotify has disabled getting audio features of tracks, so just setting all as None
						danceability=energy=key=loudness=speechiness=acousticness=instrumentalness=liveness=valence=tempo=duration_ms=None


						# #get acoustic features for each track
						# audio_features = sp.audio_features([track_id])
						# time.sleep(6)
						# try:
						# 	danceability = audio_features[0]['danceability']
						# 	energy = audio_features[0]['energy']
						# 	key = audio_features[0]['key']
						# 	loudness = audio_features[0]['loudness']
						# 	speechiness = audio_features[0]['speechiness']
						# 	acousticness = audio_features[0]['acousticness']
						# 	instrumentalness = audio_features[0]['instrumentalness']
						# 	liveness = audio_features[0]['liveness']
						# 	valence = audio_features[0]['valence']
						# 	tempo = audio_features[0]['tempo']
						# 	duration_ms = audio_features[0]['duration_ms']
						# except:
						# 	danceability=energy=key=loudness=speechiness=acousticness=instrumentalness=liveness=valence=tempo=duration_ms=None
							
						online_row_dict = {
							'track_id':track_id,
							'track_name':track_name,
							'artist_name':artist_name,
							'artist_id':artist_id,
							'date_released':date_released,
							'date_added_to_online_list': datetime.today().strftime('%Y-%m-%d'),
							'danceability':danceability,
							'energy':energy,
							'key':key,
							'loudness':loudness,
							'speechiness':speechiness,
							'acousticness':acousticness,
							'instrumentalness':instrumentalness,
							'liveness':liveness,
							'valence':valence,
							'tempo':tempo,
							'duration_ms':duration_ms,
							'combined_string': combined_string
						}

						online_rows.append(online_row_dict)
						#remember this song so we don't add it again later in this same run
						this_week_online_track_ids.add(track_id)
						this_week_online_combined_strings.append(combined_string)
						if combined_key:
							this_week_online_combined_keys.add(combined_key)

		#done processing this playlist - record its snapshot_id so that next run can
			#skip it if it hasn't changed
		if snapshot_id:
			current_snapshot_rows.append({
				'playlist_id': playlist_id,
				'snapshot_id': snapshot_id,
				'last_seen': datetime.today().strftime('%Y-%m-%d'),
			})

#now that the loop is done, build the dataframe of this week's new songs in one go
add_online_df = pd.DataFrame(online_rows, columns=column_names_online)

#sorting add_online_df by acousticness
	#i like acoustic music, this sorting allows songs that are more acoustic to appear at the top of the playlist
			#So i get to listen to the more acoustic music first
	#You can sort by any other property you want like instrumentalness, danceability etc.
add_online_df.sort_values(by='acousticness', ascending=False, inplace=True)

# wiping the slate clean, removing all tracks present in the consolidated playlist if any
sp.playlist_replace_items(playlist_id_to_update, [])

#add tracks from add_online_df to the consolidated new music playlist
# we can only add 100 at a time    
ids_to_add = add_online_df['track_id'].tolist()
len_list = len(ids_to_add)
no_of_100s = math.ceil(len_list/100)
for i in range(0, no_of_100s):
	list_100 = ids_to_add[:100]
	sp.playlist_add_items(playlist_id_to_update, list_100)
	del ids_to_add[:100]
	time.sleep(10)

#here we are adding all the songs from this week to the master_list csv    
if not add_online_df.empty:
	master_list_online_df = pd.concat([master_list_online_df, add_online_df.dropna(axis=1, how='all')], ignore_index=True, sort=False)
master_list_online_df.to_csv('master_list_online.csv', index=False, encoding='utf-8')

#save this run's playlist snapshot_ids, so that unchanged playlists can be skipped next time
save_playlist_snapshot_cache(current_snapshot_rows, SNAPSHOT_CACHE_PATH)

# Below is the code to notify you when the playlist is ready for listening
	# This is for anyone who's scheduled the script to run every week at a specific time using cron
	# this email lets you know when the update's done
		# If you run the script manually on demand, this email portion wont be useful to you
	# you can also do things like phone notifications using pushbullet https://pypi.org/project/pushbullet.py/
	# email code lifted from https://realpython.com/python-send-email/#sending-fancy-emails , 
			#https://stackoverflow.com/questions/882712/sending-html-email-using-python and various other stackoverflow posts
			
	# IF YOU WANT EMAIL NOTIFICATIONS, UNCOMMENT EVERYTHING BELOW THIS LINE

# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import configparser

# config = configparser.ConfigParser()
# config.read('config_email.ini')

# receiver_email = config['info']['email'] 
# sender_email = config['info']['sender_email'] 
# sender_password = config['info']['sender_password'] 

# message = MIMEMultipart()
# message["From"] = sender_email
# message["To"] = receiver_email

# today = datetime.today().strftime('%b %d, %Y')

# message["Subject"] = "Playlist update done — " + today

# htmlx = "<html>Update done. Open the <a style='color: blue' href='https://open.spotify.com/user/{}/playlist/{}'>playlist</a>.</html>".format(current_user_id, playlist_id_to_update)
# part1 = MIMEText(htmlx, "html")
# message.attach(part1)

# s = smtplib.SMTP('smtp.gmail.com', 587)
# s.ehlo()
# s.starttls() 
# s.login(sender_email, sender_password)
# s.sendmail(sender_email, receiver_email, message.as_string()) 
# s.quit()
