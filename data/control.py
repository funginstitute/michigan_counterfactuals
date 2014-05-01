"""
First, we run this query

select patent.id, location.state, rawinventor.inventor_id from patent 
left join rawinventor on rawinventor.patent_id = patent.id 
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id 
left join location on location.id = rawlocation.location_id 
where 
year(patent.date) < 1986;

Then, we group the records together by patent number. We only want inventors
who are from
'AK', 'CA', 'CT', 'MN', 'MT', 'NB', 'NV', 'OK', 'WA', 'WV'
"""

import pandas as pd
c = pd.read_csv('control2.csv',delimiter='\t')

states = ['AK', 'CA', 'CT', 'MN', 'MT', 'NB', 'NV', 'OK', 'WA', 'WV']

g = c.groupby('id').groups

# saved patents
controlset = []

for group in g:
    skip = False
    for row in g[group]:
        if c.loc[row]['state'] not in states:
            skip = True
            break
    if not skip:
        controlset.append(group)
    skip = False

pd.Series(controlset).to_csv('controlpatents',index=False)

