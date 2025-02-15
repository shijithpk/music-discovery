
import asyncio
from playwright.async_api import async_playwright
from lxml import html
import pandas as pd
import random
import logging
from datetime import datetime
import os
import csv
import pytz

ist = pytz.timezone('Asia/Kolkata')

# Get the current timestamp in the desired format
timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

# Set up logging
logging.basicConfig(filename=f'logs/{timestamp}_app.log', level=logging.INFO, format='%(message)s')

# path_timestamp = datetime.now().strftime("%I_%M_%p")
path_timestamp = datetime.now(ist).strftime("%I_%M_%p")

csv_path = 'data/mla_basic_data_post_detailed.csv'
dump_csv = f'data/all_candidates_data_{path_timestamp}.csv'

name_replacement_dict ={
	'Independent': 'Ind.',
	'Indian National Congress': "CONG",
}

def createPartySname(partyFname):
	if partyFname in name_replacement_dict:
		return name_replacement_dict[partyFname]
	else:
		return ''.join([char for char in partyFname if char.isupper() or char in "()"])

url_start = 'https://results.eci.gov.in/ResultAcGenFeb2025/candidateswise-'


async def get_page_content(page, url, retries=3, delay=5):
	for i in range(retries):
		try:
			await page.goto(url)
			content = await page.content()
			return content
		except Exception as e:
			logging.error(f"Failed to get content from {url} on attempt {i+1}: {e}")
			if i < retries - 1:
				await asyncio.sleep(delay)
	logging.error(f"Failed to get content from {url} after {retries} attempts")
	return None

async def process_page(url, page, row, writer, state_code):
	seat_name = row['seat_name']
	seat_id = row['seat_id']
	url_for_checking = url

	content = await get_page_content(page, url_for_checking)
	if content is None:
		logging.info(f"Issue with: {url_for_checking}")
		return

	root = html.fromstring(content)

	info_boxes = root.xpath("//div[@class='cand-info']")

	total_votes = 0

	for box in info_boxes:
		num_votes_raw = box.xpath(".//div[contains(@class,'status') and not(contains(@class,'round-status'))]/div[span]/text()")[0].strip()
		num_votes = int(num_votes_raw)
		total_votes += num_votes

	candidates_data = []

	for box in info_boxes:
		cand_name_raw = box.xpath(".//div[@class='nme-prty']/h5/text()")[0]
		cand_name = cand_name_raw.title()

		cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

		cand_votes_raw = box.xpath(".//div[contains(@class,'status') and not(contains(@class,'round-status'))]/div[span]/text()")[0].strip()
		cand_votes = int(cand_votes_raw)

		cand_party_short = createPartySname(cand_party)
	
		cand_vote_share_percent = round(100*(cand_votes/total_votes),1)

		candidates_data.append([seat_id, seat_name, url_for_checking, cand_name, cand_party, cand_party_short, cand_votes, total_votes, cand_vote_share_percent])

	candidates_data.sort(key=lambda x: x[6], reverse=True)

	# Write the sorted and ranked data to the CSV file
	for i, data in enumerate(candidates_data, start=1):
		writer.writerow(data + [i])  # Add the rank to the data

async def run_all(seats_df, dump_csv):
	async with async_playwright() as p:
		browser = await p.webkit.launch()
		context = await browser.new_context()
		page = await context.new_page()

		with open(dump_csv, 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['seat_id', 'seat_name', 'url_for_checking', 'cand_name', 'cand_party', 'cand_party_short', 'cand_votes', 'total_votes', 'cand_vote_share_percent', 'cand_position'])

			for index, row in seats_df.iterrows():
				# state_code = row['st_code_eci']
				state_code = 'U05' # for delhi
				seat_code = row['seat_id']
				
				url_string = url_start + state_code + seat_code + '.htm'
				delay = random.uniform(0.75, 1.25)
				await asyncio.sleep(delay)
				await process_page(url_string, page, row, writer, state_code)

		await context.close()
		await browser.close()


# Main execution
if __name__ == "__main__":

	col_data_types = {'seat_id': 'object'}
	seats_df = pd.read_csv(csv_path, dtype=col_data_types)

	# asyncio.run(run_all(seats_df.head(5), dump_csv)) # for testing
	asyncio.run(run_all(seats_df, dump_csv))


# cd /home/ubuntu/work/spotify_management_redux/scraping_2025_02_08_delhi && /usr/bin/python3 ./get_cand_data_v2.py