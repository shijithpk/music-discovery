#!/usr/bin/env python3

from datetime import datetime
from datetime import timedelta
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyOAuth
import cred_spotify
import math
import pandas as pd
import spotipy
import time

scope = "playlist-read-private playlist-modify-private playlist-modify-public playlist-modify-public"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred_spotify.client_id , client_secret= cred_spotify.client_secret ,redirect_uri=cred_spotify.redirect_url, scope=scope, open_browser=False))

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


# wiping the slate clean, removing all tracks present in the consolidated playlist
sp.playlist_replace_items(playlist_id_to_update, [])

now = datetime.now()
current_year = str(now.year)

playlist_ids_df = pd.read_csv('playlist_ids.csv')
master_list_online_df = pd.read_csv('master_list_online.csv')
    #this master_list_online_df is the list we will check for duplicates against

#creating a dataframe that we will be merging with the master list online dataframe later on
column_names_online = ['track_id', 'track_name', 'artist_name', 'artist_id', 'date_released',
       'date_added_to_online_list', 'danceability', 'energy', 'key',
       'loudness', 'speechiness', 'acousticness', 'instrumentalness',
       'liveness', 'valence', 'tempo', 'duration_ms', 'combined_string']
add_online_df = pd.DataFrame(columns = column_names_online)

for index,row in playlist_ids_df.iterrows():
    playlist_id = row['playlist_id']
    playlist_name = row['playlist_name']
    source = row['source']

    # here we are getting all the tracks of a constitutent playlist
    results = sp.playlist_items(playlist_id, offset=0, market='IN')
    items = results['items']
    while results['next']:
        time.sleep(6)
        results = sp.next(results)
        items.extend(results['items'])

    for item in items:
        if item['track']:
            track_name = item['track']['name']
            track_id = item['track']['id']
            artist_name_list = [artist['name'] for artist in item['track']['artists']]
            artist_name = ', '.join(artist_name_list)
            combined_string = track_name + ' ' + artist_name
            artist_id_list = [artist['id'] for artist in item['track']['artists']]
            artist_id = ', '.join(artist_id_list)
            album_name = item['track']['album']['name']
            album_id = item['track']['album']['id']
            date_released = item['track']['album']['release_date']
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
                        #by looking at the track id in the master list , 
                            # also by checking whether another playlist this week has the same track id
                            # also by doing fuzzy matches. If it's a score less than 100, we can add it
                                # am ok with duplicates in the list, not ok with missing out on tracks

                    if ((track_id not in master_list_online_df['track_id'].tolist()) and \
                        (track_id not in add_online_df['track_id'].tolist()) and \
                        (fuzz.partial_token_set_ratio(master_list_online_df['combined_string'], combined_string) < 100) and \
                        (fuzz.partial_token_set_ratio(add_online_df['combined_string'], combined_string) < 100)):
                            #if there is no track with a different id that is a fuzzy match of the track we are looking at, we can add it

                            #get acoustic features for each track
                            audio_features = sp.audio_features([track_id])
                            time.sleep(6)

                            danceability = audio_features[0]['danceability']
                            energy = audio_features[0]['energy']
                            key = audio_features[0]['key']
                            loudness = audio_features[0]['loudness']
                            speechiness = audio_features[0]['speechiness']
                            acousticness = audio_features[0]['acousticness']
                            instrumentalness = audio_features[0]['instrumentalness']
                            liveness = audio_features[0]['liveness']
                            valence = audio_features[0]['valence']
                            tempo = audio_features[0]['tempo']
                            duration_ms = audio_features[0]['duration_ms']

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

                            add_online_df = add_online_df.append(online_row_dict, ignore_index = True)

#sorting add_online_df by acousticness
    #i like acoustic music, this sorting allows songs that are more acoustic to appear at the top of the playlist
    #you can sort by any other property you want like energy, danceability etc.
add_online_df.sort_values(by='acousticness', ascending=False, inplace=True)

#add tracks from add_online_df to consolidated new music playlist
ids_to_add = add_online_df['track_id'].tolist()
len_list = len(ids_to_add)
no_of_100s = math.ceil(len_list/100)
for i in range(0, no_of_100s):
    list_100 = ids_to_add[:100]
    sp.playlist_add_items(playlist_id_to_update, list_100)
    time.sleep(10)
    del ids_to_add[:100]

master_list_online_df = pd.concat([master_list_online_df, add_online_df], ignore_index=True, sort=False)
master_list_online_df.to_csv('master_list_online.csv', index=False, encoding='utf-8')

# Below is the code to notify you when the playlist is ready for listening
    # This is for anyone who's scheduled the script to run every week at a specific time using cron
    # this email lets you know when the update's done
        # If you run the script manually on demand, this email portion wont be useful to you
    # you can also do things like phone notifications instead using pushbullet https://pypi.org/project/pushbullet.py/
    # email code lifted from https://realpython.com/python-send-email/#sending-fancy-emails , 
            #https://stackoverflow.com/questions/882712/sending-html-email-using-python and various other stackoverflow posts
    # IF YOU DONT WANT ANY EMAIL NOTIFICATIONS, YOU CAN JUST COMMENT OUT EVERYTHING BELOW THIS LINE

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

config = configparser.ConfigParser()
config.read('config_email.ini')

receiver_email = config['info']['email'] 
sender_email = config['info']['sender_email'] 
sender_password = config['info']['sender_password'] 

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email

today = datetime.today().strftime('%Y-%m-%d')
message["Subject"] = "Playlist update done for the week " + today

plain_text = "Playlist update done for the week"
part1 = MIMEText(plain_text, "plain")
message.attach(part1)

s = smtplib.SMTP('smtp.gmail.com', 587)
s.ehlo()
s.starttls() 
s.login(sender_email, sender_password)
s.sendmail(sender_email, receiver_email, message.as_string()) 
s.quit()
