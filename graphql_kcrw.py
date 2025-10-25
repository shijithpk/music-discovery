import requests
import json
import math
import time

# --- CONFIGURATION ---
# Set the total number of latest episodes you want to download.
EPISODES_TO_FETCH = 10 

# The maximum number of items the API allows per request. 100 is a common and safe limit.
API_PAGE_LIMIT = 100

# The ID for the show you want to scrape.
SHOW_ID = "519be39fa61573099bae0012350a0a4d"
# -------------------


# --- CORE COMPONENTS (from your curl command) ---
url = 'https://graphql.contentful.com/content/v1/spaces/2658fe8gbo8o/environments/master'
headers = {
	'accept': 'application/graphql-response+json, application/json',
	'authorization': 'Bearer ESmpg32ilfpRrOLHQlHq8OjQc268hBta-wZBCOJc4lY',
	'content-type': 'application/json',
	'origin': 'https://www.kcrw.com',
	'referer': 'https://www.kcrw.com/',
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
}
query = """
query ShowEpisodesById($id: String!, $limit: Int = 1, $skip: Int = 0, $sorting: [StoryOrder], $preview: Boolean) {
  storyCollection(
	where: {shows: {sys: {id: $id}}, isSegment_not: true, contentfulMetadata: {concepts: {descendants: {id_contains_none: "hidden"}}}}
	limit: $limit
	skip: $skip
	order: $sorting
	preview: $preview
  ) {
	total
	items {
	  __typename
	  ...EpisodeFragment
	}
  }
}
fragment EpisodeFragment on Story {
  sys { id }
  showsCollection(limit: 1) { items { title slug } }
  bylineDate
  title
  slug
  shortDescription
  primaryImage { asset { url } altText }
  categoriesCollection(where: {sys: {publishedVersion_exists: true}}, limit: 3) { items { title } }
  audioMedia { mediaUrl duration }
  videoMedia { mediaUrl duration }
  hostsCollection(limit: 3) { items { name } }
}
"""
# ----------------------------------------------------


def scrape_episodes():
	"""
	Fetches a specified number of the latest episodes, handling pagination automatically.
	"""
	all_episodes = []
	
	try:
		# First, let's get the total number of available episodes to be safe.
		print("Checking total number of available episodes...")
		initial_payload = {
			"query": query,
			"variables": {"id": SHOW_ID, "limit": 1, "skip": 0},
			"operationName": "ShowEpisodesById"
		}
		response = requests.post(url, headers=headers, json=initial_payload)
		response.raise_for_status()
		total_available = response.json()['data']['storyCollection']['total']
		print(f"Found {total_available} total episodes available for this show.")

		# Determine the actual number of episodes to fetch (can't fetch more than exist)
		episodes_to_fetch_actual = min(EPISODES_TO_FETCH, total_available)
		if episodes_to_fetch_actual < EPISODES_TO_FETCH:
			print(f"Warning: You requested {EPISODES_TO_FETCH}, but only {total_available} are available. Fetching all available.")
		
		print(f"Starting download of {episodes_to_fetch_actual} episodes...")

		# Loop until we have collected the desired number of episodes
		while len(all_episodes) < episodes_to_fetch_actual:
			remaining_to_fetch = episodes_to_fetch_actual - len(all_episodes)
			
			# Calculate limit for this specific request
			# It's the smaller of the API limit or the number we still need
			limit_for_this_request = min(API_PAGE_LIMIT, remaining_to_fetch)
			
			variables = {
				"limit": limit_for_this_request,
				"skip": len(all_episodes), # Skip the ones we already have
				"sorting": "bylineDate_DESC",
				"id": SHOW_ID,
				"preview": False
			}
			
			payload = {
				"query": query,
				"variables": variables,
				"operationName": "ShowEpisodesById"
			}

			print(f"Fetching {limit_for_this_request} episodes (total collected: {len(all_episodes)})...")
			page_response = requests.post(url, headers=headers, json=payload)
			page_response.raise_for_status()
			
			new_items = page_response.json()['data']['storyCollection']['items']
			
			# Safety break: if the API returns no items, stop to prevent an infinite loop
			if not new_items:
				print("API returned no more items. Stopping.")
				break
				
			all_episodes.extend(new_items)
			time.sleep(1) # Be polite to the server

		print(f"\nScraping complete! Successfully downloaded data for {len(all_episodes)} episodes.")

		# Save the data to a file
		output_filename = f'kcrw_latest_{len(all_episodes)}_episodes.json'
		with open(output_filename, 'w', encoding='utf-8') as f:
			json.dump(all_episodes, f, ensure_ascii=False, indent=2)
		
		print(f"Data saved to {output_filename}")

	except requests.exceptions.RequestException as e:
		print(f"An error occurred during the request: {e}")
	except KeyError as e:
		print(f"Could not find key {e} in the response. The API structure might have changed.")
		if 'response' in locals():
			print("Response content:", response.text)

# Run the scraper
if __name__ == "__main__":
	scrape_episodes()