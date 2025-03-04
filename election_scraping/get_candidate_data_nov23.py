
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

def assignAlliance(party_full, state_code):
	alliance_mapping = {
		# S13 for maharashtra
		'S13':{
			"Independent": "OTHERS",

			"Indian National Congress": "Maha Vikas Aghadi (CONG+)",
			"Shiv Sena (Uddhav Balasaheb Thackeray)": "Maha Vikas Aghadi (CONG+)",
			"Nationalist Congress Party – Sharadchandra Pawar": "Maha Vikas Aghadi (CONG+)",
			"Nationalist Congress Party - Sharadchandra Pawar": "Maha Vikas Aghadi (CONG+)",
			"Samajwadi Party": "Maha Vikas Aghadi (CONG+)",
			"Peasants And Workers Party of India": "Maha Vikas Aghadi (CONG+)",
			"Communist Party of India (Marxist)": "Maha Vikas Aghadi (CONG+)",
			"Communist Party of India  (Marxist)": "Maha Vikas Aghadi (CONG+)",
			"Communist Party of India": "Maha Vikas Aghadi (CONG+)",

			"Bharatiya Janata Party": "Mahayuti (BJP+)",
			'Shiv Sena': "Mahayuti (BJP+)",
			"Nationalist Congress Party": "Mahayuti (BJP+)",
			"Jan Surajya Shakti": "Mahayuti (BJP+)",
			"Jan Surajya Shakti Paksha": "Mahayuti (BJP+)",
			"Jan Surajya Shakti Party": "Mahayuti (BJP+)",
			"Rashtriya Yuva Swabhiman Party": "Mahayuti (BJP+)",
			"Rajarshi Shahu Vikas Aghadi": "Mahayuti (BJP+)",
			"Rashtriya Samaj Paksha": "Mahayuti (BJP+)",
			"Rashtriya Samaj Party": "Mahayuti (BJP+)",
			"Republican Party of India (Athavale)": "Mahayuti (BJP+)",

			},
		#S27 for jharkhand	
		'S27':{
			"Independent": "OTHERS",

			"Bharatiya Janata Party": "NDA",
			"AJSU Party": "NDA",
			"Lok Janshakti Party(Ram Vilas)": "NDA",
			"Janata Dal (United)": "NDA",

			"Jharkhand Mukti Morcha": "Mahagathbandhan (JMM+)",
			"Indian National Congress": "Mahagathbandhan (JMM+)",
			"Communist Party of India (Marxist-Leninist) (Liberation)": "Mahagathbandhan (JMM+)",
			"Rashtriya Janata Dal": "Mahagathbandhan (JMM+)",

			},	
	}
	
	# return alliance_mapping.get(party_full, "OTHERS")
	return alliance_mapping[state_code].get(party_full, "OTHERS")

# Get the current timestamp in the desired format
timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

# Set up logging
logging.basicConfig(filename=f'logs/{timestamp}_app.log', level=logging.INFO, format='%(message)s')

# path_timestamp = datetime.now().strftime("%I_%M_%p")
path_timestamp = datetime.now(ist).strftime("%I_%M_%p")


csv_path = 'data/mla_basic_data_postPoll_en_detailed.csv'
dump_csv = f'data/all_candidates_data_{path_timestamp}.csv'

name_replacement_dict ={
	'Independent': 'Ind.',
	'Jammu & Kashmir Peoples Democratic Party': "PDP",
	'Jammu & Kashmir National Conference': "NC",

	# UPDATED VALUES FOR MH AND JH ELECTIONS 
	'Maharashtra Navnirman sena': "MNS",
	'Nationalist Congress Party – Sharadchandra Pawar': "NCP(SP)",
	'Nationalist Congress Party - Sharadchandra Pawar': "NCP(SP)",
	'Swabhimani Paksha': "SWP",
	'All India Majlis-E-Ittehadul Muslimeen': "AIMIM",
	'AJSU Party': "AJSUP",

}

def createPartySname(partyFname):
	if partyFname in name_replacement_dict:
		return name_replacement_dict[partyFname]
	else:
		return ''.join([char for char in partyFname if char.isupper() or char in "()"])

# url_start = 'https://results.eci.gov.in/AcResultGenOct2024/candidateswise-'
url_start = 'https://results.eci.gov.in/ResultAcGenNov2024/candidateswise-'
# CHANGE URL ON SATURDAY


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
	state_name = row['state_id']
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

		alliance = assignAlliance(cand_party, state_code)

		candidates_data.append([seat_name, state_name, url_for_checking, cand_name, cand_party, cand_party_short, cand_votes, total_votes, cand_vote_share_percent, alliance])

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
			writer.writerow(['seat_name', 'state_name', 'url_for_checking', 'cand_name', 'cand_party', 'cand_party_short', 'cand_votes', 'total_votes', 'cand_vote_share_percent', 'alliance', 'cand_position'])

			for index, row in seats_df.iterrows():
				state_code = row['st_code_eci']
				seat_code = row['seat_id']
				
				url_string = url_start + state_code + seat_code + '.htm'
				delay = random.uniform(0.75, 1.25)
				await asyncio.sleep(delay)
				await process_page(url_string, page, row, writer, state_code)

		await context.close()
		await browser.close()


# Main execution
if __name__ == "__main__":

	col_data_types = {'seat_id': 'object', 'st_code_eci': 'object'}
	seats_df = pd.read_csv(csv_path, dtype=col_data_types)

	# asyncio.run(run_all(seats_df.head(5), dump_csv)) # for testing
	asyncio.run(run_all(seats_df, dump_csv))


# cd /home/ubuntu/work/spotify_management_redux/election_scraping && /usr/bin/python3 ./get_candidate_data_nov23.py >> /home/ubuntu/work/spotify_management_redux/election_scraping/logs/`date +\%Y-\%m-\%d-\%H:\%M`-get-cand-data.log 2>&1