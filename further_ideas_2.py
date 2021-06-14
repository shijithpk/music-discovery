#!/usr/bin/env python3

from datetime import datetime
from datetime import timedelta
from fuzzywuzzy import fuzz
from spotipy.oauth2 import SpotifyOAuth
import cred
import math
import pandas as pd
import spotipy
import time

scope = "playlist-read-private playlist-modify-private playlist-modify-public playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cred.client_id , client_secret= cred.client_secret ,redirect_uri=cred.redirect_url, scope=scope, open_browser=False))

#REMOVING all TRACKS FROM NEW MUSIC PLAYLIST
    #NEW MUSIC PLAYLIST ID '3XidTKBIpsGymPCjlN7kZH' https://open.spotify.com/playlist/3XidTKBIpsGymPCjlN7kZH
sp.playlist_replace_items('3XidTKBIpsGymPCjlN7kZH', [])

now = datetime.now()
current_year = str(now.year)

#START A NEW LIST FOR THE NEW YEAR
    #if you're in the first seven days of January, time to start a new list
day_of_year = now.timetuple().tm_yday
if 1 <= day_of_year <= 7:
    new_playlist_title = current_year + '_master_list_1'
    sp.user_playlist_create('shijith', new_playlist_title, public=False, collaborative=False, description='Songs compiled from new music lists of various publications, websites and radio stations')


#ok check how many lists have YEAR_master_list in their title?
    #take the latest one
    #use that as the playlist you update throughout
    #dont hardcode the spotify id

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
search_string = current_year + '_master_list_'
matching_titles = [s for s in playlist_name_list if search_string in s]
number_matching_titles = len(matching_titles)
playlist_title_to_update = search_string + str(number_matching_titles)
playlist_id_to_update = name_id_dict[playlist_title_to_update]

#CHECK IF ADDING SONGS WILL TAKE LIST OVER 10000 limit
    #Basically if number of rows over 9000, time to start a new playlist
    # if adding the songs takes it over the 10000 songs limit for a spotify playlist, dont add to this one, just start another spotify playlist and add songs to that
results = sp.playlist_items(playlist_id_to_update, offset=0, market='IN')
items = results['items']
while results['next']:
    time.sleep(5)
    results = sp.next(results)
    items.extend(results['items'])
number_items_playlist = len(items)
if number_items_playlist > 9000:
    playlist_title_to_create = search_string + str(number_matching_titles + 1)
    new_playlist = sp.user_playlist_create('shijith', playlist_title_to_create,  public=False, collaborative=False, 
            description='Songs compiled from new music lists of various publications, websites and radio stations')
    #replacing earlier value of playlist_id_to_update
    playlist_id_to_update = new_playlist["id"]


playlist_ids_df = pd.read_csv('playlist_ids.csv')
master_list_df = pd.read_csv('master_list.csv')
master_list_online_df = pd.read_csv('master_list_online.csv')
    #this master_list_online_df will become useful later on
    #since there might be 2-3 master lists in a year on spotify, its useful to have one list with all the tracks from all the master lists online
        # its a list that we can check for duplicates against

#columns in master_list_df
column_names_local = ['playlist_id', 'playlist_name', 'source', 'track_name', 'track_id',
       'artist_name', 'artist_id', 'album_name', 'album_id', 'date_released',
       'date_added_to_playlist', 'date_added_to_master_list']

#columns in master_list_online_df
column_names_online = ['track_id', 'track_name', 'artist_name', 'artist_id', 'date_released',
       'date_added_to_online_list', 'danceability', 'energy', 'key',
       'loudness', 'speechiness', 'acousticness', 'instrumentalness',
       'liveness', 'valence', 'tempo', 'duration_ms', 'combined_string']

#creating dataframes that we will be merging with the two master list dataframes later on
add_locally_df = pd.DataFrame(columns = column_names_local)
add_online_df = pd.DataFrame(columns = column_names_online)

for index,row in playlist_ids_df.iterrows():
    playlist_id = row['playlist_id']
    playlist_name = row['playlist_name']
    source = row['source']
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

            local_row_dict = {
                'playlist_id': playlist_id, 
                'playlist_name' : playlist_name, 
                'source' : source, 
                'track_name' : track_name, 
                'track_id' : track_id,
                'artist_name' : artist_name, 
                'artist_id' : artist_id, 
                'album_name' : album_name, 
                'album_id' : album_id, 
                'date_released' : date_released,
                'date_added_to_playlist' : date_added_to_playlist, 
                'date_added_to_master_list' : date_added_to_master_list
                }

            if not ((master_list_df['playlist_id'] == playlist_id) & (master_list_df['track_id'] == track_id)).any():
                #meaning an entry with this track under this playlist is not already there
                #there is a possibility that track id is there in 
                    #master_list_df but under a different playlist, but that's ok
                
                # Lots of old songs just have a year in release date, need a check to see if date released string length is 10 characters
                if len(date_released) == 10:
                    date_released_object = datetime.strptime(date_released, '%Y-%m-%d')
                    days_since_release = now - date_released_object

                    #if released this year or in last two months
                    if (current_year in date_released) or (days_since_release < timedelta(weeks = 9)):

                        add_locally_df = add_locally_df.append(local_row_dict, ignore_index = True)

                        if ((track_id not in master_list_online_df['track_id'].tolist()) and \
                            (track_id not in add_online_df['track_id'].tolist()) and \
                            (fuzz.partial_token_set_ratio(master_list_online_df['combined_string'], combined_string) < 100) and \
                            (fuzz.partial_token_set_ratio(add_online_df['combined_string'], combined_string) < 100)):
                                #so there is no track with a different id that is a fuzzy match of the track we want to add
 
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

#sort add_online_df by acousticness
add_online_df.sort_values(by='acousticness', ascending=False, inplace=True)

#add tracks from add_online_df to spotify
    #add to acoustic master list online
    #add to new acoustic music list online
ids_to_add = add_online_df['track_id'].tolist()
len_list = len(ids_to_add)
no_of_100s = math.ceil(len_list/100)
for i in range(0, no_of_100s):
    list_100 = ids_to_add[:100]
    sp.playlist_add_items(playlist_id_to_update, list_100)
    time.sleep(10)
    #also adding to new music playlist
    sp.playlist_add_items('3XidTKBIpsGymPCjlN7kZH', list_100)
    time.sleep(10)
    del ids_to_add[:100]

master_list_online_df = pd.concat([master_list_online_df, add_online_df], ignore_index=True, sort=False)
master_list_online_df.to_csv('master_list_online.csv', index=False, encoding='utf-8')

master_list_df = pd.concat([master_list_df, add_locally_df], ignore_index=True, sort=False)
master_list_df.to_csv('master_list.csv', index=False, encoding='utf-8')


#CHECK FOR PLAYLISTS THAT HAVENT UPDATED RECENTLY
# * in the code if a playlist hasnt been updated in 6 weeks, make note of it and send email about it
# 	* then make call about whether playlist has to be removed or let it be for now (sometimes these playlists dont get updated over summer, xmas holidays, so those time periods ok as exceptions, otherwise not ok)



master_list_df_new = pd.read_csv('master_list.csv')
new_df = master_list_df_new[['playlist_id','source','playlist_name','date_added_to_playlist']]\
.sort_values('date_added_to_playlist')\
.groupby(['playlist_id','source','playlist_name']).tail(1).reset_index(drop=True)

#these are playlists i added earlier but removed later on. Dont want to include them in the email
playlists_to_ignore = ['2fACkXaMF5AkjudREQHqME','7L9bFJhsV08162AZEYr1BH']

new_df = new_df[~new_df['playlist_id'].isin(playlists_to_ignore)]
new_df['date_of_last_update'] = pd.to_datetime(new_df['date_added_to_playlist'], format='%Y-%m-%d')
new_df.rename(columns = {'playlist_id':'spotify_playlist_id', 'source':'playlist_source'}, inplace = True)
new_df.drop(['date_added_to_playlist'], axis=1, inplace = True)
new_df['days_since_last_update'] = (now - new_df['date_of_last_update']).dt.days

#email code lifted from https://realpython.com/python-send-email/#sending-fancy-emails , 
        #https://stackoverflow.com/questions/882712/sending-html-email-using-python and various other stackoverflow posts

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#rename config_RENAME.ini in your directory to config.ini

receiver_email = config['info']['email'] 
sender_email = config['info']['sender_email'] 
sender_password = config['info']['sender_password'] 

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email

today = datetime.today().strftime('%Y-%m-%d')
message["Subject"] = "Playlist update done for the week " + today

# plain_text = "Playlist update done for the week"
# part1 = MIMEText(plain_text, "plain")
# message.attach(part1)

htmlx = "<html><h2>LAST UPDATE FOR EACH PLAYLIST</h2>{}</html>".format(new_df.to_html())
part1 = MIMEText(htmlx, "html")
message.attach(part1)

s = smtplib.SMTP('smtp.gmail.com', 587)
s.ehlo()
s.starttls() 
#if tls isn't working, try ssl and secure context
s.login(sender_email, sender_password)
s.sendmail(sender_email, receiver_email, message.as_string()) 
s.quit()
