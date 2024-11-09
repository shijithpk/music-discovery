#!/usr/bin/env python3

import requests
import re 
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred
import time
import pandas as pd
from lxml import html
import json
from datetime import datetime
import random
import unidecode
from itertools import combinations
from thefuzz import fuzz

scope = "playlist-read-private playlist-modify-private playlist-modify-public user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred.client_id , client_secret= cred.client_secret ,redirect_uri=cred.redirect_url, scope=scope, open_browser=False))


playlist_dict = {
	'radio2_folk_show':{'playlist_id':'5DjFGSMemnQlto1iopbULA'},
	'radio3_music_planet':{'playlist_id':'197QzBV7LFn6o4rFbUe1kJ'},
	'radio1_rock_show':{'playlist_id':'2rjHoY4rckW70ChgsK1JUc'},
	'radio6_the_morning_after_mix':{'playlist_id':'3OFAXHgkjxsJ1tGBBzKWCt'},
	'radio1_the_chillest_show':{'playlist_id':'4x1Qroq1N7F4mwsfKC2oPJ'},
	'radio6_gilles_peterson_show':{'playlist_id':'2hh8x1bPsgPpxwhIV0muAn'}, 
	'radio6_new_music':{'playlist_id':'32uSQvONpNRWU2bPxHkjhj'},
}

missing_shows_dict = {
	'radio2_folk_show': [		
		'https://www.bbc.co.uk/programmes/m0023xgz',
		'https://www.bbc.co.uk/programmes/m0023qfz',
		'https://www.bbc.co.uk/programmes/m0023fzk',
		'https://www.bbc.co.uk/programmes/m00235qp',
		'https://www.bbc.co.uk/programmes/m0022zs2',
		'https://www.bbc.co.uk/programmes/m0022q3v',
		'https://www.bbc.co.uk/programmes/m0022k2q',
		'https://www.bbc.co.uk/programmes/m00228vt',
		'https://www.bbc.co.uk/programmes/m00222g2',
		'https://www.bbc.co.uk/programmes/m0021wj4',
		'https://www.bbc.co.uk/programmes/m0021wbl',

	],
	'radio3_music_planet': [
		'https://www.bbc.co.uk/programmes/m00244wj',
		'https://www.bbc.co.uk/programmes/m0023xz9',
		'https://www.bbc.co.uk/programmes/m0023dzq',
		'https://www.bbc.co.uk/programmes/m00236cp',
		'https://www.bbc.co.uk/programmes/m00230cj',
		'https://www.bbc.co.uk/programmes/m0022ld3',
		'https://www.bbc.co.uk/programmes/m0021xzh',
	],
	'radio1_rock_show': [
		'https://www.bbc.co.uk/programmes/m0023vfz',
		'https://www.bbc.co.uk/programmes/m0023lmg',
		'https://www.bbc.co.uk/programmes/m0023ctx',
		'https://www.bbc.co.uk/programmes/m00235hx',
		'https://www.bbc.co.uk/programmes/m0022xml',
		'https://www.bbc.co.uk/programmes/m0022ryc',
		'https://www.bbc.co.uk/programmes/m0022hdk',
		'https://www.bbc.co.uk/programmes/m00228y6',
		'https://www.bbc.co.uk/programmes/m00224yw',
		'https://www.bbc.co.uk/programmes/m0021tht',
	],
	'radio6_the_morning_after_mix': [
		'https://www.bbc.co.uk/programmes/m00245rp',
		'https://www.bbc.co.uk/programmes/m0023w5w',
		'https://www.bbc.co.uk/programmes/m0023nzq',
		'https://www.bbc.co.uk/programmes/m0023fyz',
		'https://www.bbc.co.uk/programmes/m00234g9',
		'https://www.bbc.co.uk/programmes/m00230dh',
		'https://www.bbc.co.uk/programmes/m0022pyk',
		'https://www.bbc.co.uk/programmes/m0022lvx',
		'https://www.bbc.co.uk/programmes/m0022lvv',
		'https://www.bbc.co.uk/programmes/m00221b9',
		'https://www.bbc.co.uk/programmes/m001w8wl',
	],
	'radio1_the_chillest_show': [
		'https://www.bbc.co.uk/programmes/m0023v9z',
		'https://www.bbc.co.uk/programmes/m0023ll1',
		'https://www.bbc.co.uk/programmes/m0023cnp',
		'https://www.bbc.co.uk/programmes/m00235l5',
		'https://www.bbc.co.uk/programmes/m0022xp2',
		'https://www.bbc.co.uk/programmes/m0022rt5',
		'https://www.bbc.co.uk/programmes/m0022j9l',
		'https://www.bbc.co.uk/programmes/m00228z7',
		'https://www.bbc.co.uk/programmes/m00224xv',
		'https://www.bbc.co.uk/programmes/m0021tgl',
	],
	'radio6_gilles_peterson_show': [
		'https://www.bbc.co.uk/programmes/m00245rc',
		'https://www.bbc.co.uk/programmes/m0023w5h',
		'https://www.bbc.co.uk/programmes/m0023nz3',
		'https://www.bbc.co.uk/programmes/m0023fyn',
		'https://www.bbc.co.uk/programmes/m00234fx',
		'https://www.bbc.co.uk/programmes/m00230d3',
		'https://www.bbc.co.uk/programmes/m0022py2',
		'https://www.bbc.co.uk/programmes/m0022hn1',
		'https://www.bbc.co.uk/programmes/m00228q1',
		'https://www.bbc.co.uk/programmes/m002219z',
		'https://www.bbc.co.uk/programmes/m0021y08',
	], 
	'radio6_new_music': [
		'https://www.bbc.co.uk/programmes/m0023w7w',
		'https://www.bbc.co.uk/programmes/m0023q94',
		'https://www.bbc.co.uk/programmes/m0023g0j',
		'https://www.bbc.co.uk/programmes/m00234kd',
		'https://www.bbc.co.uk/programmes/m00230mf',
		'https://www.bbc.co.uk/programmes/m0022q72',
		'https://www.bbc.co.uk/programmes/m0022hsd',
		'https://www.bbc.co.uk/programmes/m00229vj',
		'https://www.bbc.co.uk/programmes/m00221l8',
		'https://www.bbc.co.uk/programmes/m0021wk3',
	],
}

# output_data = {}

for show in playlist_dict:
	# output_data[show] = {}
	playlist_id = playlist_dict[show]['playlist_id']
	missing_shows = missing_shows_dict[show]
	missing_shows.reverse()


	for show_url in missing_shows:

		track_spotify_id_list = []
		
		# output_data[show][show_url] = []
		time.sleep(random.randint(2, 5))

		response = requests.get(show_url)
		tree = html.fromstring(response.content)
		track_list = tree.xpath("//div[@class='segment__track']")
		for track in track_list:	
			artists = track.xpath(".//span[@class='artist']/text()")
			artist_string = ", ".join(artists)		
			track_name = track.xpath("normalize-space(.//p)")

			keywords = f"{artist_string} {track_name}"
			# output_data[show][show_url].append(keywords)

			keywords_normalized = unidecode.unidecode(keywords)
			keywords_no_punc = re.sub(r'[^\w\s]', '', keywords_normalized)
			keywords_list = keywords_no_punc.split()
			#ignore one-letter strings
			keywords_list_long_strings = [keywordx for keywordx in keywords_list if len(keywordx) > 1]
			string_combos = [keywords_list_long_strings]            
			len_keywords_list_long_strings = len(keywords_list_long_strings)
			if len_keywords_list_long_strings >= 4:
				#if no result at first, use combinations of words from the query
					#these combinations come after the full query containing all the keywords
				string_combos_additional = list(combinations(keywords_list_long_strings, (len_keywords_list_long_strings - 1)))
				string_combos.extend(string_combos_additional)
			if len_keywords_list_long_strings >= 5:
				string_combos_additional_2 = list(combinations(keywords_list_long_strings, (len_keywords_list_long_strings - 2)))
				string_combos.extend(string_combos_additional_2)
			if len_keywords_list_long_strings >= 6:
				string_combos_additional_3 = list(combinations(keywords_list_long_strings, (len_keywords_list_long_strings - 3)))
				string_combos.extend(string_combos_additional_3)
			for combo in string_combos:
				time.sleep(8)
				query = ' '.join(combo)
				results = sp.search(query, limit=1, offset=0, type="track", market='IN')
				#if results not empty
				if results['tracks']['items']:
					track_id_from_search = results['tracks']['items'][0]['id']
					search_artist_name_list = [artist['name'] for artist in results['tracks']['items'][0]['artists']]
					search_artist = ', '.join(search_artist_name_list)
					search_title = results['tracks']['items'][0]['name']
					search_artist_title_combined = search_artist + ' ' + search_title
					level_of_match = fuzz.token_set_ratio(keywords, search_artist_title_combined)
					if level_of_match >= 85:
						track_spotify_id_list.append(track_id_from_search)
						break

		sp.playlist_add_items(playlist_id, track_spotify_id_list, position=0)

# with open('bbc_shows_tracks.json', 'w', encoding='utf-8') as f:
# 	json.dump(output_data, f, indent=4, ensure_ascii=False)

# cd /home/ubuntu/work/spotify_management_redux && /usr/bin/python3 ./bbc_add_missing_months.py >> /home/ubuntu/work/spotify_management_redux/cron_logs/`date +\%Y-\%m-\%d-\%H:\%M`-missing-months-cron.log 2>&1