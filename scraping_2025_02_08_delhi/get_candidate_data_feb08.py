import subprocess
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright
from lxml import html
import pandas as pd
import random
import logging
import os
import json
from pathlib import Path
import pytz

csv_path = 'data/mla_basic_data_post_detailed.csv'

ist = pytz.timezone('Asia/Kolkata')
path_timestamp = datetime.now(ist).strftime("%I_%M_%p")
dump_csv_path = f'data/seat_data_{path_timestamp}.csv'


# CHANGE URL ON SATURDAY
# url_start = 'https://results.eci.gov.in/ResultAcGenNov2024/candidateswise-'
url_start = 'https://results.eci.gov.in/ResultAcGenFeb2025/candidateswise-'

timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
logging.basicConfig(filename=f'logs/{timestamp}_app.log', level=logging.INFO, format='%(message)s')

name_replacement_dict ={
	'Indian National Congress': "CONG",
	'Independent': 'Ind.',

	'Nationalist Congress Party – Sharadchandra Pawar': "NCP(SP)",
	'Nationalist Congress Party - Sharadchandra Pawar': "NCP(SP)",
	'All India Majlis-E-Ittehadul Muslimeen': "AIMIM",

}


def createPartySname(partyFname):
	if partyFname in name_replacement_dict:
		return name_replacement_dict[partyFname]
	else:
		return ''.join([char for char in partyFname if char.isupper() or char in "()"])


async def get_page_content(url, context):	
	try:
		page = await context.new_page()
		await page.goto(url)
		content = await page.content()
		await page.close()
		return content
	except Exception as e:
		logging.error(f"Failed to get content from {url}: {e}")
		return None


async def process_page(url, context):	
	url_for_checking = url
	logging.info(f"Processing page: {url}")
	content = await get_page_content(url, context)
	if content is None:
		return
	root = html.fromstring(content)

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
			partySname = createPartySname(cand_party)

		property_dict = {
						'mla_name_en': cand_name,
						'party_full': cand_party,
						'party_short': partySname,
						'declared_winner_yes_no': 'yes',
						'total_votes': None,
						'leader_votes': None,
						'leader_vote_share_pc': None,
						'loserName': None,
						'loserParty': None,
						'loserPartySname': None,
						'loser_votes': None,
						'loser_vote_share_pc': None,
						'lead_margin_votes': None,
						'lead_margin_vote_share_pc': None,
						'url_for_checking': url_for_checking,
					}
		
		return property_dict
	
	else:

		total_votes = 0

		leader = None
		leader_party = None
		leader_votes = 0

		second_leader = None
		second_leader_party = None
		second_leader_votes = 0

		try:

			for box in info_boxes:
				cand_name_raw = box.xpath(".//div[@class='nme-prty']/h5/text()")[0]
				cand_name = cand_name_raw.title()

				cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

				num_votes_raw = box.xpath(".//div[contains(concat(' ', normalize-space(@class), ' '), ' status ') and not(contains(concat(' ', normalize-space(@class), ' '), ' round-status '))]/div[span]/text()")[0].strip()
				num_votes = int(num_votes_raw)

				total_votes += num_votes

				if num_votes > leader_votes:
					second_leader_votes = leader_votes
					second_leader = leader
					second_leader_party = leader_party

					leader_votes = num_votes
					leader = cand_name
					leader_party = cand_party

					won_condition_1 = box.xpath(".//div[contains(@class, 'status') and contains(@class, 'won')]")
					won_condition_2 = box.xpath(".//div[contains(@class, 'status')]/div[contains(@style, 'text-transform: capitalize') and contains(text(),'won')]")
					
				elif num_votes > second_leader_votes:
					second_leader_votes = num_votes
					second_leader = cand_name
					second_leader_party = cand_party

			mla_name_en = leader
			party_full = leader_party
			party_short = createPartySname(leader_party)
			leader_vote_share_pc = round(100*leader_votes/total_votes,1)

			loserName = second_leader
			loser_votes = second_leader_votes
			loserParty = second_leader_party
			loserPartySname = createPartySname(loserParty)
			loser_vote_share_pc = round(100*second_leader_votes/total_votes,1)

			lead_margin_votes = leader_votes - second_leader_votes
			lead_margin_vote_share_pc = round(leader_vote_share_pc - loser_vote_share_pc,1)

			if won_condition_1 or won_condition_2:
				declared_winner_yes_no = 'yes'
			else:
				declared_winner_yes_no = 'no'



			property_dict = {
				'mla_name_en': mla_name_en,
				'party_full': party_full,
				'party_short': party_short,
				'declared_winner_yes_no': declared_winner_yes_no,
				'total_votes': total_votes,
				'leader_votes': leader_votes,
				'leader_vote_share_pc': leader_vote_share_pc,
				'loserName': loserName,
				'loserParty': loserParty,
				'loserPartySname': loserPartySname,
				'loser_votes': loser_votes,
				'loser_vote_share_pc': loser_vote_share_pc,
				'lead_margin_votes': lead_margin_votes,
				'lead_margin_vote_share_pc': lead_margin_vote_share_pc,
				'url_for_checking': url_for_checking,
			}

		except:
			property_dict = None

		return property_dict

async def run_all(csv_path):	
	async with async_playwright() as p:
		browser = await p.webkit.launch()
		context = await browser.new_context(is_mobile=False, ignore_https_errors=True)

		col_data_types = {'seat_id': 'object'}

		with open(csv_path, 'r') as file:
			seats_df = pd.read_csv(file, dtype=col_data_types)

		for index, row in seats_df.iterrows():
			state_code = 'U05' # for delhi
			seat_code = row['seat_id']
			url_string = url_start + state_code + seat_code + '.htm'
			delay = random.uniform(0.85, 1.35)
			await asyncio.sleep(delay)
			property_dict = await process_page(url_string, context)

			if property_dict is not None:
				seats_df.loc[index,'leader_name'] = property_dict['mla_name_en']
				seats_df.loc[index,'leader_party_full'] = property_dict['party_full']
				seats_df.loc[index,'leader_party_short'] = property_dict['party_short']
				seats_df.loc[index,'declared_winner_yes_no'] = property_dict['declared_winner_yes_no']
				seats_df.loc[index,'total_votes'] = property_dict['total_votes']
				seats_df.loc[index,'leader_votes'] = property_dict['leader_votes']
				seats_df.loc[index,'leader_vote_share_pc'] = property_dict['leader_vote_share_pc']
				seats_df.loc[index,'loser_name'] = property_dict['loserName']
				seats_df.loc[index,'loser_party_full'] = property_dict['loserParty']
				seats_df.loc[index,'loser_party_short'] = property_dict['loserPartySname']
				seats_df.loc[index,'loser_votes'] = property_dict['loser_votes']
				seats_df.loc[index,'loser_vote_share_pc'] = property_dict['loser_vote_share_pc']
				seats_df.loc[index,'lead_margin_votes'] = property_dict['lead_margin_votes']
				seats_df.loc[index,'lead_margin_vote_share_pc'] = property_dict['lead_margin_vote_share_pc']
				seats_df.loc[index,'url_for_checking'] = property_dict['url_for_checking']

		# saving detailed csv 
		with open(dump_csv_path, 'w') as file:
			seats_df.to_csv(file, index=False)

		await context.close()
		await browser.close()

asyncio.run(run_all(csv_path))


# /home/ubuntu/work/spotify_management_redux/scraping_2025_02_08_delhi/get_candidate_data_feb08.py

# 5,25,45 * * * * cd /home/ubuntu/work/data_website_v2/static/assets_v2/polls-2025 && /usr/bin/python3 ./update_csv_feb8.py

# cd /home/ubuntu/work/spotify_management_redux/scraping_2025_02_08_delhi && /usr/bin/python3 ./get_candidate_data_feb08.py