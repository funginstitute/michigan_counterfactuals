import pandas as pd

tcites = pd.read_csv('cites_to_controlused.tsv',delimiter='\t')

tdata = pd.read_csv('control_usedmetadata.tsv',delimiter='\t')
tdata = tdata.drop_duplicates(cols=['number'])

merged = pd.merge(tdata, tcites, left_on='number', right_on='cited', how='right')
merged = merged[merged['assignee_id_x'] != merged['assignee_id_y']]
merged = merged[merged['state_x'] != merged['state_y']]
print merged.head()
merged[['citing','cited','citing_year','state_x']].drop_duplicates().to_csv('control_usedcites.tsv',index=False,sep='\t')
