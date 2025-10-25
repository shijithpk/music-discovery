#!/home/ubuntu/py313/bin/python

import time
import spotify_utils
import pandas as pd
import re
from playwright.sync_api import sync_playwright
from lxml import html

# Global settings
DELAY = 8  # Delay between Spotify API calls (seconds)
THRESHOLD = 90  # Match threshold for Spotify search
POSITION = 0  # Position to add tracks (0 for top)

# Initialize Spotify client
sp = spotify_utils.initialize_spotify()

def process_page(page_config, playwright_page):

	track_ids = []

	url = page_config['page_url']
	container_xpath = page_config['container_xpath']
	artist_xpath = page_config['artist_xpath']
	song_xpath = page_config['song_xpath']

	playlist_id = page_config['playlist_id']

	# page = requests.get(url)	
	# Using playwright_page.goto() with 'domcontentloaded' is a good start, but for JS-heavy sites,
	# it's not enough. The DOM might be loaded, but the content isn't rendered yet.
	playwright_page.goto(url, wait_until='domcontentloaded')

	# **KEY CHANGE**: Wait for the main container element to be present in the DOM.
	# This ensures the JavaScript has run and rendered the content we need to scrape.
	# We'll wait for up to 30 seconds (the default timeout).
	# print(f"Waiting for selector: {container_xpath}")
	playwright_page.wait_for_selector(container_xpath)

	content = playwright_page.content()
	tree = html.fromstring(content)

	container_list = tree.xpath(container_xpath)

	for container in container_list:
		artist = container.xpath(artist_xpath)[0].text_content().strip()
		if song_xpath:
			song = container.xpath(song_xpath)[0].text_content().strip()
		else:
			song = ''

		artist_song = artist + ' ' + song

		search_result = spotify_utils.search_track(sp, artist, song, delay=DELAY, match_threshold=THRESHOLD)

		if search_result:
			track_id, spotify_title, spotify_artist, match_level = search_result
			track_ids.append(track_id)

		else:
			print(f"  ✗ No match found for: {artist_song}")

	if track_ids:
		unique_track_ids = spotify_utils.filter_existing_tracks(sp, playlist_id, track_ids, delay=DELAY)

		if unique_track_ids:

			# Reverse the entire list of track IDs
			unique_track_ids.reverse()
	
			for i in range(0, len(unique_track_ids), 100):
				batch = unique_track_ids[i:i+100]
				
				# Reverse the batch to maintain original order when added at position 0
				batch.reverse()
				
				try:
					sp.playlist_add_items(playlist_id, batch, position=POSITION)
					time.sleep(DELAY)

				except Exception as e:
					print(f"Error adding tracks to playlist: {e}")

		else:
			print("All found tracks are already in the playlist. Nothing to add.")

	else:
		print("No tracks found to add to playlist")


PAGES = {
	'radio2_playlist':{
		'page_url': "https://www.bbc.co.uk/programmes/articles/2qNJsnjYFvbLrK9CZ0CfYfM/radio-2-new-music-playlist",
		'container_xpath': "//div[contains(@class, 'component__body')]/div[contains(@class, 'text--prose')]/p",
		'artist_xpath': ".",
		"song_xpath": "",
		'playlist_id': "4sOoJdciQNwcJSj0cgJ6DY",
		# https://open.spotify.com/playlist/4sOoJdciQNwcJSj0cgJ6DY?si=c1f7537c333f4cef
	},
	'kcrw_top_five_this_week': {
		'page_url': "http://email.kcrw.com/5-songs-to-hear",
		'container_xpath': "//td[ contains(@class, 'tile') ]",
		'artist_xpath': "(.//a[ contains(@href,'youtube') and normalize-space(text()) and @data-hs-link-id ])[1]",
		"song_xpath": "(.//a[ contains(@href,'youtube') and normalize-space(text()) and @data-hs-link-id ])[2]",
		"playlist_id": "5NJ8NiOnW7gSSsAQQs7I5n",
		# https://open.spotify.com/playlist/5NJ8NiOnW7gSSsAQQs7I5n?si=29c0d8deecf64ee6
	},
	'kcrw_todays_top_tune': {
		'page_url': "https://www.kcrw.com/shows/todays-top-tune/all-episodes",
		'container_xpath': "//article",
		'artist_xpath': ".//h3[contains(@class,'header')]",
		"song_xpath": "",
		"playlist_id": "4hnFH5DBSCdnmV8lfDBo3F",
		# https://open.spotify.com/playlist/4hnFH5DBSCdnmV8lfDBo3F?si=195ca0eac5224491
	},
}

with sync_playwright() as p:
	browser = p.chromium.launch()
	playwright_page = browser.new_page()

	# Process each feed
	for page_name, page_config in PAGES.items():
		try:
			process_page(page_config, playwright_page)
		except Exception as e:
			print(f"Error processing feed {page_name}: {e}")
	
	browser.close()


# DO WE NEED MORE ERROR LOGGING IN THIS SCRIPT?

# cd /home/ubuntu/work/spotify_management_redux && /home/ubuntu/py313/bin/python ./url_to_playlist.py >> /home/ubuntu/work/cron_logs/`date +\%Y-\%m-\%d-\%H:\%M`-url-playlist-cron.log 2>&1