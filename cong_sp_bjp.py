import asyncio
from playwright.async_api import async_playwright
from lxml import html
import pandas as pd
import random
import logging
from datetime import datetime

csv_path = 'ac_seats_list_2023.csv'
col_data_types = {'AC_CODE': 'object', 'ST_CODE': 'object','st_code_eci':'object'}

seats_df = pd.read_csv(csv_path, dtype=col_data_types)

# Get the current timestamp in the desired format
timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')

# Set up logging
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
	logging.info(f"Processing page: {url}")
	content = await get_page_content(url, browser)
	if content is None:
		return
	root = html.fromstring(content)

	info_boxes = root.xpath("//div[@class='cand-info']")

	url_for_checking = url

	bjp_votes = 0
	cong_votes = 0
	sp_votes = 0
	cong_sp_beat_bjp = None
	cong_sp_win_seat = None

	winner_party = None
	winner_votes = 0
	winner_partySname = None

	try:

		for box in info_boxes:

			cand_party = box.xpath(".//div[@class='nme-prty']/h6/text()")[0]

			num_votes_raw = box.xpath(".//div[contains(@class,'status')]/div[span]/text()")[0].strip()
			num_votes = int(num_votes_raw)

			if cand_party == 'Bharatiya Janata Party':
				bjp_votes = num_votes
			elif cand_party == 'Samajwadi Party':
				sp_votes = num_votes
			elif cand_party == 'Indian National Congress':
				cong_votes = num_votes

			if num_votes > winner_votes:
				winner_votes = num_votes
				winner_party = cand_party


		if (cong_votes > 0) and (sp_votes > 0) and (bjp_votes > 0):
			if cong_votes + sp_votes > bjp_votes:
				cong_sp_beat_bjp = 'yes'
			elif cong_votes + sp_votes < bjp_votes:
				cong_sp_beat_bjp = 'no'
			elif cong_votes + sp_votes == bjp_votes:
				cong_sp_beat_bjp = 'tie'

		if (cong_votes > 0) and (sp_votes > 0) and (winner_party != 'Indian National Congress') and (winner_party != 'Samajwadi Party'):
			if cong_votes + sp_votes > winner_votes:
				cong_sp_win_seat = 'yes'
			elif cong_votes + sp_votes < winner_votes:
				cong_sp_win_seat = 'no'
			elif cong_votes + sp_votes == winner_votes:
				cong_sp_win_seat = 'tie'

		if winner_party == 'Indian National Congress':
			cong_sp_win_seat = 'Cong won by itself'
		elif winner_party == 'Samajwadi Party':
			cong_sp_win_seat = 'SP won by itself'

		if winner_party == 'Independent':
			winner_partySname = 'Ind.'
		else:
			winner_partySname = ''.join([char for char in winner_party if char.isupper() or char in "()"])


		property_dict = {
			'url_for_checking': url_for_checking,
			'winner_partySname': winner_partySname,
			'winner_votes': winner_votes,
			'cong_votes' : cong_votes,
			'sp_votes' : sp_votes,
			'bjp_votes' : bjp_votes,
			'cong_sp_beat_bjp': cong_sp_beat_bjp,
			'cong_sp_win_seat': cong_sp_win_seat
		}

	except:
		property_dict = None

	return property_dict

async def run_all(seats_df, csv_path):
	async with async_playwright() as p:
		browser = await p.webkit.launch()

		st_code_eci = '12'

		for index, row in seats_df.iterrows():
			state_code = row['st_code_eci']
			if state_code != st_code_eci:
				continue
			seat_code = row['AC_CODE']
			url_string = 'https://results.eci.gov.in/AcResultGenDecNew2023/candidateswise-S' + state_code + seat_code + '.htm'
			delay = random.uniform(0.75, 1.25)
			await asyncio.sleep(delay)
			property_dict = await process_page(url_string, browser)

			if property_dict is not None:
				seats_df.loc[index,'url_for_checking'] = property_dict['url_for_checking']
				seats_df.loc[index,'winner_partySname'] = property_dict['winner_partySname']
				seats_df.loc[index,'winner_votes'] = property_dict['winner_votes']
				seats_df.loc[index,'cong_votes'] = property_dict['cong_votes']
				seats_df.loc[index,'sp_votes'] = property_dict['sp_votes']
				seats_df.loc[index,'bjp_votes'] = property_dict['bjp_votes']
				seats_df.loc[index,'cong_sp_beat_bjp'] = property_dict['cong_sp_beat_bjp']
				seats_df.loc[index,'cong_sp_win_seat'] = property_dict['cong_sp_win_seat']

		seats_df.to_csv(csv_path, index=False)

		await browser.close()

asyncio.run(run_all(seats_df, csv_path))