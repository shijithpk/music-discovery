import pandas as pd

# Read the original CSV
df = pd.read_csv('/home/ubuntu/work/spotify_management_redux/scraping_2025_02_08_delhi/data/all_candidates_data_06_19_PM.csv')

# Create a new dataframe with unique seats
result_df = df[['seat_id', 'seat_name']].drop_duplicates()

# Calculate AAP+CONG votes
aap_cong_df = df[df['cand_party_short'].isin(['AAP', 'CONG'])].groupby('seat_id')['cand_votes'].sum().reset_index(name='AAP_CONG_combined')

# Calculate BJP votes
bjp_df = df[df['cand_party_short'] == 'BJP'].groupby('seat_id')['cand_votes'].sum().reset_index(name='BJP_votes')



# Merge all dataframes
result_df = (result_df
			 .merge(aap_cong_df, on='seat_id', how='left')
			 .merge(bjp_df, on='seat_id', how='left'))

# Add the comparison column
result_df['more_than_BJP'] = result_df.apply(
	lambda row: 'YES' if row['AAP_CONG_combined'] > row['BJP_votes'] else 'NO',
	axis=1
)

# Add the winner column
winners = df[df['cand_position'] == 1][['seat_id', 'cand_party_short']].rename(columns={'cand_party_short': 'WON_BY'})
result_df = result_df.merge(winners, on='seat_id', how='left')

# Add the new column with conditional logic
result_df['more_than_BJP_not_won'] = result_df.apply(
	lambda row: 'YES' if (row['more_than_BJP'] == 'YES' and row['WON_BY'] not in ['AAP', 'CONG']) else '',
	axis=1
)

# Drop the BJP_votes column if you don't need it
# result_df = result_df.drop('BJP_votes', axis=1)

# Save the new CSV
output_path = '/home/ubuntu/work/spotify_management_redux/scraping_2025_02_08_delhi/data/seat_wise_analysis.csv'
result_df.to_csv(output_path, index=False)
