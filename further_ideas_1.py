#!/usr/bin/env python3

# code from https://gist.github.com/riebschlager/831b914ce53d6f14c20d3cb1945fb9bb
# my kcrw metropolis playlist is at https://open.spotify.com/playlist/39s1hlg987JGqOeXkmuUUn

import requests
from datetime import date
from dateutil.relativedelta import relativedelta, SA
from datetime import datetime
import re 
import unidecode
from itertools import combinations
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cred
import time
import pandas as pd

scope = "playlist-read-private playlist-modify-private playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred.client_id , client_secret= cred.client_secret ,redirect_uri=cred.redirect_url, scope=scope,open_browser=False))

#counting number of tracks in metropolis playlist
results = sp.playlist_items('39s1hlg987JGqOeXkmuUUn', offset=0, market='IN')
items = results['items']
while results['next']:
    time.sleep(5)
    results = sp.next(results)
    items.extend(results['items'])


#delete last 40 items if number of tracks in metropolis playlist over 9960
#since tracks from updates are inserted at the top, the oldest tracks will be at the bottom and will be removed
if len(items) >= 9960:
    last_40_items = items[-40:]
    last_40_ids = []
    for item in last_40_items:
        track_idx = item['track']['id']
        last_40_ids.append(track_idx)

    sp.playlist_remove_all_occurrences_of_items('39s1hlg987JGqOeXkmuUUn', last_40_ids)

#we dont have to specify date, will set cron to run the script on sundays at 09:00 UTC
today = date.today()
last_sat_date_object = today + relativedelta(weekday = SA(-1))
last_sat_date = last_sat_date_object.strftime('%Y/%m/%d')

api_url = 'https://tracklist-api.kcrw.com/Simulcast/date/' + last_sat_date

track_spotify_id_list = []

column_names = ['metropolis title', 'metropolis artist', 'search title','search artist']
df_for_mail = pd.DataFrame(columns = column_names)

response = requests.get(api_url)
track_list = response.json()
for track in track_list:
    if track['program_title']== 'Metropolis':
        track_spotify_id = track['spotify_id']
        #There are spotify ids given in api response sometimes
            #for songs that dont have spotify ids, we do a search for them on spotify later
        if track_spotify_id != '':
            track_spotify_id_list.append(track_spotify_id)
        elif track['title'] != '':
            #creating a dictionary with default value as empty string
                # will append this dict to the empty dataframe and send the whole thing across in an email             
            row_dict = dict.fromkeys(column_names, '')
            
            track_artist = track['artist']
            track_title = track['title']
            #storing this info for the mail, lets me know which ones didnt have a spotify id and we searched for a match on spotify
            
            row_dict['metropolis title'] = track_title
            row_dict['metropolis artist'] = track_artist

            # query = "artist:" + track_artist + " track:" + track_title
            # results = sp.search(query, limit=1, offset=0, type="track", market='IN')
            # Am not going to use field filters (like artist:) in search query, not getting right results
            # will try and simulate how users type queries in spotify search field, ie. without field filters or operators
                #think their search is optimized for how regular people type queries
            keywords = track_artist + ' ' + track_title
            keywords_normalized = unidecode.unidecode(keywords)
            keywords_no_punc = re.sub(r'[^\w\s]', '', keywords_normalized)
            keywords_list = keywords_no_punc.split()
            #remove strings of less than three letters
            keywords_list_long_strings = [keywordx for keywordx in keywords_list if len(keywordx) > 2]
            string_combos = [keywords_list_long_strings]            
            len_keywords_list_long_strings = len(keywords_list_long_strings)
            if len_keywords_list_long_strings >= 3:
                #if no result at first, use combinations of words from the query
                    #these combinations come after the full query containing all the keywords
                string_combos_additional = list(combinations(keywords_list_long_strings, (len_keywords_list_long_strings - 1)))
                string_combos.extend(string_combos_additional)
            if len_keywords_list_long_strings >= 4:
                string_combos_additional_2 = list(combinations(keywords_list_long_strings, (len_keywords_list_long_strings - 2)))
                string_combos.extend(string_combos_additional_2)
            for combo in string_combos:
                time.sleep(8)
                query = ' '.join(combo)
                results = sp.search(query, limit=1, offset=0, type="track", market='IN')
                #if results not empty
                if results['tracks']['items']:
                    track_id_from_search = results['tracks']['items'][0]['id']
                    track_spotify_id_list.append(track_id_from_search)

                    search_artist_name_list = [artist['name'] for artist in results['tracks']['items'][0]['artists']]
                    search_artist = ', '.join(search_artist_name_list)
                    search_title = results['tracks']['items'][0]['name']
                    row_dict['search title'] = search_title
                    row_dict['search artist'] = search_artist

                    break
            
            df_for_mail = df_for_mail.append(row_dict, ignore_index=True)


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#rename config_SAMPLE.ini in your directory to config.ini

receiver_email = config['info']['email'] 
sender_email = config['info']['sender_email'] 
sender_password = config['info']['sender_password'] 

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email

today = datetime.today().strftime('%Y-%m-%d')
message["Subject"] = "Metropolis tracks missing spotify ids " + today

htmlx = "<html><h2>LAST UPDATE FOR EACH PLAYLIST</h2>{}</html>".format(df_for_mail.to_html())
part1 = MIMEText(htmlx, "html")
message.attach(part1)

s = smtplib.SMTP('smtp.gmail.com', 587)
s.ehlo()
s.starttls() 
#if tls isn't working, try ssl and secure context
s.login(sender_email, sender_password)
s.sendmail(sender_email, receiver_email, message.as_string()) 
s.quit()

sp.playlist_add_items('39s1hlg987JGqOeXkmuUUn', reversed(track_spotify_id_list), position=0)