import asyncio
from playwright.async_api import async_playwright
from lxml import html
import pandas as pd
import random
import logging
from datetime import datetime
import os

orig_csv = 'ac_seats_list_2023.csv'
col_data_types = {'AC_CODE': 'object', 'st_code_eci':'object'}
orig_df_raw = pd.read_csv(orig_csv, dtype=col_data_types)
orig_df = orig_df_raw[['AC_CODE','AC_NAME','ST_NAME_NEW','st_code_eci']]
orig_df.to_csv(orig_csv, index=False)

seats_df = pd.read_csv(orig_csv, dtype=col_data_types)

if not os.path.exists('logs'):
	os.makedirs('logs')

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

logging.basicConfig(filename=f'logs/{timestamp}_app.log', level=logging.INFO, format='%(message)s')

async def get_page_content(url, browser):
	try:
		page = await browser.new_page()
		await page.goto(url)
		content = await page.content()
		await page.close()
		return content
	except Exception as e:
		logging.error(f"Failed to get content from {url}: {e}")
		return None

async def process_page(url, browser):
	url_for_checking = url

	content = await get_page_content(url, browser)
	if content is None:
		logging.info(f"Issue with: {url}")
		return

	root = html.fromstring(content)

	info_boxes = root.xpath("//div[@class='cand-info']")

	total_votes = 0
	nota_votes = 0
	nota_over_win_margin = None
	leader_votes = 0
	leader = None
	leader_party = None
	second_leader_votes = 0
	second_leader = None
	second_leader_party = None

	try:

		for box in info_boxes:
			cand_name_raw = box.xpath(".//div[@class='nme-prty']/h5/text()")[0]
			cand_name = cand_name_raw.title()

			cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

			num_votes_raw = box.xpath(".//div[contains(@class,'status')]/div[span]/text()")[0].strip()
			num_votes = int(num_votes_raw)

			if cand_party == 'None of the Above':
				nota_votes = num_votes

			total_votes += num_votes

			if num_votes > leader_votes:
				second_leader_votes = leader_votes
				second_leader = leader
				second_leader_party = leader_party

				leader_votes = num_votes
				leader = cand_name
				leader_party = cand_party

			elif num_votes > second_leader_votes:
				second_leader_votes = num_votes
				second_leader = cand_name
				second_leader_party = cand_party

		winnerName = leader
		partyFname = leader_party
		if partyFname == 'Independent':
			winnerPartySname = 'Ind.'
		else:
			winnerPartySname = ''.join([char for char in partyFname if char.isupper() or char in "()"])

		loserName = second_leader
		loserParty = second_leader_party
		if loserParty == 'Independent':
			loserPartySname = 'Ind.'
		else:
			loserPartySname = ''.join([char for char in loserParty if char.isupper() or char in "()"])

		win_margin_votes = leader_votes - second_leader_votes

		if nota_votes > 0:
			if nota_votes > win_margin_votes:
				nota_over_win_margin = 'yes'
			else:
				nota_over_win_margin = 'no'
		else:
			nota_over_win_margin = None

		nota_vote_share_percent = round(100*(nota_votes/total_votes),1)

		property_dict = {
			'url_for_checking': url_for_checking,
			'winnerName' : winnerName,
			'winnerPartySname' : winnerPartySname,
			'loserName' : loserName,
			'loserPartySname' : loserPartySname,
			'win_margin_votes': win_margin_votes,
			'nota_votes': nota_votes,
			'nota_over_win_margin': nota_over_win_margin,
			'total_votes': total_votes,
			'nota_vote_share_percent': nota_vote_share_percent
		}

	except:
		property_dict = None

	return property_dict

async def run_all(seats_df, orig_csv):
	async with async_playwright() as p:
		browser = await p.webkit.launch()

		for st_code_eci in ['20','12','29','26']:

			for index, row in seats_df.iterrows():
				state_code = row['st_code_eci']
				if state_code != st_code_eci:
					continue
				seat_code = row['AC_CODE']
				if (st_code_eci == '20') and (seat_code == '3'):
					continue
				url_string = 'https://results.eci.gov.in/AcResultGenDecNew2023/candidateswise-S' + state_code + seat_code + '.htm'
				delay = random.uniform(0.75, 1.25)
				await asyncio.sleep(delay)
				property_dict = await process_page(url_string, browser)

				if property_dict is not None:
					seats_df.loc[index,'url_for_checking'] = property_dict['url_for_checking']
					seats_df.loc[index,'winnerName'] = property_dict['winnerName']
					seats_df.loc[index,'winnerPartySname'] = property_dict['winnerPartySname']
					seats_df.loc[index,'loserName'] = property_dict['loserName']
					seats_df.loc[index,'loserPartySname'] = property_dict['loserPartySname']
					seats_df.loc[index,'win_margin_votes'] = property_dict['win_margin_votes']
					seats_df.loc[index,'nota_votes'] = property_dict['nota_votes']
					seats_df.loc[index,'nota_over_win_margin'] = property_dict['nota_over_win_margin']
					seats_df.loc[index,'total_votes'] = property_dict['total_votes']
					seats_df.loc[index,'nota_vote_share_percent'] = property_dict['nota_vote_share_percent']

			seats_df.to_csv(orig_csv, index=False)
				
		await browser.close()

asyncio.run(run_all(seats_df, orig_csv))


# /home/ubuntu/work/spotify_management_redux/nota_check.py

# cd /home/ubuntu/work/spotify_management_redux && /usr/bin/python3 ./nota_check.py >> /home/ubuntu/work/spotify_management_redux/logs/`date +\%Y-\%m-\%d-\%H:\%M`-nota.log 2>&1

