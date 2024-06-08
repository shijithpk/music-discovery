import asyncio
from playwright.async_api import async_playwright
from lxml import html
import pandas as pd
import random
import logging
from datetime import datetime
import os
import csv

orig_csv = 'ls_seats_list_2024_detailed.csv'

path_timestamp = datetime.now().strftime("%I_%M_%p")

dump_csv = f'candidate_data_{path_timestamp}.csv'

col_data_types = {'PC_CODE': 'object', 'ST_CODE': 'object','st_code_eci':'object','pc_code_eci':'object'}

seats_df = pd.read_csv(orig_csv, dtype=col_data_types)

if not os.path.exists('logs'):
	os.makedirs('logs')

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
logging.basicConfig(filename=f'logs/{timestamp}_app.log', level=logging.INFO, format='%(message)s')


async def get_page_content(page, url, retries=3, delay=5):
	for i in range(retries):
		try:
			await page.goto(url)
			content = await page.content()
			return content
		except Exception as e:
			logging.error(f"Failed to get content from {url} on attempt {i+1}: {e}")
			if i < retries - 1:  # no delay on the last attempt
				await asyncio.sleep(delay)
	logging.error(f"Failed to get content from {url} after {retries} attempts")
	return None


async def process_page(url, page, row, writer):
	seat_name = row['PC_NAME_NEW']
	state_name = row['ST_NAME_NEW']
	url_for_checking = url

	content = await get_page_content(page, url_for_checking)
	if content is None:
		logging.info(f"Issue with: {url_for_checking}")
		return

	root = html.fromstring(content)

	# check for uncontested seat 
	uncontested_elem_list = root.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' status ') and not(contains(concat(' ', normalize-space(@class), ' '), ' round-status '))]//div[contains(text(),'Uncontested')]")
	if len(uncontested_elem_list) > 0:
		uncontested = True
	else:
		uncontested = False

	info_boxes = root.xpath("//div[@class='cand-info']")


	if uncontested == True:	

		for box in info_boxes:

			cand_name_raw = box.xpath(".//div[@class='nme-prty']/h5/text()")[0]
			cand_name = cand_name_raw.title()

			cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

			if cand_party == 'Independent':
				partySname = 'Ind.'
			else:
				partySname = ''.join([char for char in cand_party if char.isupper() or char in "()"])

		writer.writerow([seat_name, state_name, url_for_checking, cand_name, 
				cand_party, partySname, 0, 0, 0, 1])

		# ['seat_name', 'state_name','url_for_checking', 'cand_name', 'cand_party', 'cand_party_short','cand_votes', 'total_votes', 'cand_vote_share_percent','cand_position']

	else:

		total_votes = 0

		for box in info_boxes:
			num_votes_raw = box.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' status ') and not(contains(concat(' ', normalize-space(@class), ' '), ' round-status '))]/div[span]/text()")[0].strip()
			num_votes = int(num_votes_raw)

			total_votes += num_votes

		candidates_data = []

		for box in info_boxes:
			cand_name_raw = box.xpath(".//div[@class='nme-prty']/h5/text()")[0]
			cand_name = cand_name_raw.title()

			cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

			cand_votes_raw = box.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' status ') and not(contains(concat(' ', normalize-space(@class), ' '), ' round-status '))]/div[span]/text()")[0].strip()

			cand_votes = int(cand_votes_raw)

			if cand_party == 'Independent':
				cand_party_short = 'Ind.'
			elif cand_party == 'None of the Above':
				cand_party_short = 'NOTA'
			else:
				cand_party_short = ''.join([char for char in cand_party if char.isupper() or char in "()"])

			cand_vote_share_percent = round(100*(cand_votes/total_votes),1)

			candidates_data.append([seat_name, state_name,url_for_checking, cand_name, cand_party, cand_party_short,cand_votes, total_votes, cand_vote_share_percent])


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
			writer.writerow(['seat_name', 'state_name','url_for_checking', 'cand_name', 'cand_party', 'cand_party_short','cand_votes', 'total_votes', 'cand_vote_share_percent','cand_position'])

			for index, row in seats_df.iterrows():
			# for index, row in seats_df.head(2).iterrows():

				state_code = row['st_code_eci']
				seat_code = row['pc_code_eci']

				# if state_code == 'S06' and seat_code in ['23', '24', '25']:

				url_string = 'https://results.eci.gov.in/PcResultGenJune2024/candidateswise-' + state_code + seat_code + '.htm'
				delay = random.uniform(0.85, 1.15)
				await asyncio.sleep(delay)
				await process_page(url_string, page, row, writer)

				# else:
				# 	continue

		await context.close()
		await browser.close()

asyncio.run(run_all(seats_df, dump_csv))


# /home/ubuntu/work/spotify_management_redux/scrape_final_position.py

# cd /home/ubuntu/work/spotify_management_redux && /usr/bin/python3 ./scrape_final_position.py