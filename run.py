import pandas as pd

from matplotlib import pyplot as plt
from scipy.stats import mode

from sqlalchemy import create_engine, MetaData, Table, inspect, VARCHAR, Column
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker

from datetime import datetime
import sys

engine = create_engine('mysql+mysqldb://root:330Ablumhall@169.229.7.251/usptofixed?charset=utf8')
metadata = MetaData(engine)

#NOTE: treatment = MI patents, control = nonenforce state patents

#TODO: use LOCATION, not RAWLOCATION

getsession = sessionmaker(bind=engine)

"""
the input file 'michigandistances.csv' contains 3 columns:
    'michigan': Michigan patent granted before 1985,
    'similar': patent similar to the michigan patent,
    'similarity': jaccard similarity (1.0 is same tags, 0.0 is all different).

file is truncated so that there are no distances below 0.2
"""


distances = pd.read_csv('michigandistances.csv')
distances['michigan'] = distances['michigan'].apply(str)
distances['similar'] = distances['similar'].apply(str)

"""
for each of the patents in the above file, we want:

    patent id, grant date, application date, assignee, number of inventors, state

For the MI patents, we only want patents where the first inventor is from Michigan
"""

# MI patent metadata

session = getsession()
session.rollback()
try:
    session.execute('drop table michigan;')
except:
    pass
t = Table('michigan', metadata, Column('number', VARCHAR(length=10), primary_key=True))
t.create()
inserts = []
for michigan_patent in distances['michigan']:
    inserts.append({'number':str(michigan_patent)})
t.insert().prefix_with("IGNORE").execute(inserts)
michigan_patent_data = session.execute("select patent.id as patent, patent.date as grant_date, \
                 application.date as application_date, rawassignee.organization as \
                 assignee, 1 as num_inventors, location.state from michigan \
                 left join patent on michigan.number = patent.id \
                 left join application on application.patent_id = patent.id \
                 left join rawassignee on rawassignee.patent_id = patent.id \
                 left join rawinventor on rawinventor.patent_id = patent.id \
                 left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                 left join location on location.id = rawlocation.location_id;").fetchall()
mpd = pd.DataFrame.from_records(michigan_patent_data)
mpd.columns = ['patent','grant date','app date','assignee','num inventors','state']
mpd['patent'] = mpd['patent'].apply(str)
"""
Here, filter so we get only patents that have only Michigan inventors
"""
non_full_michigan_patents = set(mpd[mpd['state'] != 'MI']['patent'])
full_michigan = []
for row in mpd.iterrows():
    if row[1]['patent'] not in non_full_michigan_patents:
        full_michigan.append(row[1])
mpd = pd.DataFrame.from_records(full_michigan)
mpd = mpd.drop_duplicates(['patent'])
#import IPython
#IPython.embed(user_ns=locals())
print len(mpd),"patents from MI with only Michigan inventors"

# similar patent metadata

try:
    session.execute('drop table similar;')
except:
    pass
t = Table('similar', metadata, Column('number', VARCHAR(length=10), primary_key=True))
t.create()
inserts = []
for similar_patent in distances['similar']:
    inserts.append({'number':str(similar_patent)})
t.insert().prefix_with("IGNORE").execute(inserts)
similar_patent_data = session.execute("select patent.id as patent, patent.date as grant_date, \
                 application.date as application_date, rawassignee.organization as \
                 assignee, count(*) as number_inventors, location.state from patent \
                 right join similar on similar.number = patent.id \
                 left join application on application.patent_id = patent.id \
                 left join rawassignee on rawassignee.patent_id = patent.id \
                 left join rawinventor on rawinventor.patent_id = patent.id \
                 left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                 left join location on location.id = rawlocation.location_id \
                 group by patent.id;").fetchall()
spd = pd.DataFrame.from_records(similar_patent_data)
spd.columns = ['patent','grant date','app date','assignee','num inventors','state']
spd['patent'] = spd['patent'].apply(str)
print len(spd), "similar patents"


"""
Now that we have the metadata for the michigan patents and the similar patents, we use
the distance data to pair them up so that we have:
    michigan patent + metadata, similarity, similar patent + metadata

We can then filter the dataset so that we only have similar patents whose grant date
is within 6 months of the corresponding michigan patent
"""

left = pd.merge(mpd, distances, how='right', left_on='patent', right_on='michigan')
full = pd.merge(left, spd, how='left', left_on='similar', right_on='patent')
del full['michigan']
del full['similar']
full.columns = ('patent_x','grant_date_x','application_date_x','assignee_x','number_inventors_x','state_x','similarity','patent_y','grant_date_y','application_date_y','assignee_y','number_inventors_y','state_y')
print len(full),"linked patent records"

newdata = []
for row in full.iterrows():
    michigan_date = row[1]['grant_date_x']
    similar_date = row[1]['grant_date_y']
    try:
        if abs((michigan_date - similar_date).days) <= 180: #180 days is ~6 months
            newdata.append(tuple(row[1].values))
    except AttributeError:
        pass
    except TypeError:
        pass # probably error with a null date, so we skip
joineddata_6monthwindow = pd.DataFrame.from_records(newdata)
joineddata_6monthwindow.columns = ('patent_x','grant_date_x','application_date_x','assignee_x','number_inventors_x','state_x','similarity','patent_y','grant_date_y','application_date_y','assignee_y','number_inventors_y','state_y')
joineddata_6monthwindow.sort(['patent_x','similarity'],ascending=[1,0]).to_csv('data.csv',index=False,encoding='utf-8')
print len(joineddata_6monthwindow),"pairs of records within 6 month window"

"""
Now, for each of the rows, we only want similar patents that are from a nonenforcing state (the CONTROL).

We do that with the following filter
"""
tmp = joineddata_6monthwindow
nonenforce_statefilter = (tmp['state_y'] == 'AK') | (tmp['state_y'] == 'CA') | (tmp['state_y'] == 'CT') | (tmp['state_y'] == 'MN') \
                       | (tmp['state_y'] == 'MT') | (tmp['state_y'] == 'ND') | (tmp['state_y'] == 'NV') | (tmp['state_y'] == 'OK') \
                       | (tmp['state_y'] == 'WA') | (tmp['state_y'] == 'WV')

scoped_data = tmp[nonenforce_statefilter]

"""
Now, each row in scoped data contains a pair of patents: a michigan patent and a similar patent from a nonenforcing state (that isn't michigan)
For each of these patents, we want to look at citations TO those patents from states that are
    a) not the same as the patent being cited
    b) from a nonenforcing state
"""

# get citations to michigan patents
try:
    session.execute('drop table michigan_filtered;')
except:
    pass
t = Table('michigan_filtered', metadata, Column('number', VARCHAR(length=10), primary_key=True))
t.create()
inserts = []
for mip in scoped_data['patent_x']:
    inserts.append({'number':str(mip)})
t.insert().prefix_with("IGNORE").execute(inserts)
cites_to_michigan = session.execute("select rawassignee.organization, patent.date, uspatentcitation.patent_id, citation_id, location.state from uspatentcitation \
                                     right join michigan_filtered on citation_id = michigan_filtered.number \
                                     left join patent on patent.id = uspatentcitation.patent_id \
                                     left join rawassignee on rawassignee.patent_id = uspatentcitation.patent_id \
                                     left join rawinventor on rawinventor.patent_id = uspatentcitation.patent_id \
                                     left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                                     left join location on location.id = rawlocation.location_id;").fetchall()
cites = pd.DataFrame.from_records(cites_to_michigan)
cites.columns = ['citing_patent_assignee','citing_patent_grant_date','citing_patent','michigan_patent','citing_patent_state']
cites['citing_patent'] = cites['citing_patent'].apply(str)
cites['michigan_patent'] = cites['michigan_patent'].apply(str)
tmp = mpd[['assignee','patent','state']].merge(cites, how='right', left_on='patent', right_on='michigan_patent')
cites = tmp[['citing_patent_assignee','citing_patent_grant_date','state','citing_patent','michigan_patent','citing_patent_state','assignee']]
cites.columns = ['citing_patent_assignee','citing_patent_grant_date','cited_patent_state','citing_patent','michigan_patent','citing_patent_state','cited_patent_assignee']
cites = cites[cites['citing_patent_assignee'] != cites['cited_patent_assignee']] # filter out cites by same firm
cites.index = cites['citing_patent']

# filter by nonenforce state that isn't michigan
statefilter =  ((cites['citing_patent_state'] != cites['cited_patent_state']) \
               & ((cites['citing_patent_state'] == 'AK') | (cites['citing_patent_state'] == 'CA') | (cites['citing_patent_state'] == 'CT') | (cites['citing_patent_state'] == 'MN') \
               | (cites['citing_patent_state'] == 'MT') | (cites['citing_patent_state'] == 'ND') | (cites['citing_patent_state'] == 'NV') | (cites['citing_patent_state'] == 'OK') \
               | (cites['citing_patent_state'] == 'WA') | (cites['citing_patent_state'] == 'WV') | (cites['citing_patent_state'] == 'MI')))
cites_to_michigan = cites[statefilter]
cites_to_michigan = cites_to_michigan.drop_duplicates(cols=['citing_patent','michigan_patent'])
cites_to_michigan.to_csv('cites_to_michigan.csv',index=False,encoding='utf-8')
print len(cites_to_michigan), "citations to michigan patents with matched nonenforce patents"

# get citations to the other nonenforce patents
try:
    session.execute('drop table nonenforce;')
except:
    pass
t = Table('nonenforce', metadata, Column('number', VARCHAR(length=10), primary_key=True))
t.create()
inserts = []
for mip in scoped_data['patent_y']:
    inserts.append({'number':str(mip)})
t.insert().prefix_with("IGNORE").execute(inserts)
cites_to_nonenforces = session.execute("select rawassignee.organization, patent.date, uspatentcitation.patent_id, citation_id, location.state from uspatentcitation \
                                     right join nonenforce on citation_id = nonenforce.number \
                                     left join patent on patent.id = uspatentcitation.patent_id \
                                     left join rawassignee on rawassignee.patent_id = uspatentcitation.patent_id \
                                     left join rawinventor on rawinventor.patent_id = uspatentcitation.patent_id \
                                     left join rawlocation on rawlocation.id = rawinventor.rawlocation_id \
                                     left join location on location.id = rawlocation.location_id;").fetchall()
cites = pd.DataFrame.from_records(cites_to_nonenforces)
cites.columns = ['citing_patent_assignee','citing_patent_grant_date','citing_patent','nonenforce_patent','citing_patent_state']
cites['citing_patent'] = cites['citing_patent'].apply(str)
cites['nonenforce_patent'] = cites['nonenforce_patent'].apply(str)

# now need to join on "spd" datatable
tmp = spd[['assignee','patent','state']].merge(cites, how='right', left_on='patent', right_on='nonenforce_patent')
cites = tmp[['citing_patent_assignee','citing_patent_grant_date','state','citing_patent','nonenforce_patent','citing_patent_state','assignee']]
cites.columns = ['citing_patent_assignee','citing_patent_grant_date','cited_patent_state','citing_patent','nonenforce_patent','citing_patent_state','cited_patent_assignee']
cites = cites[cites['citing_patent_assignee'] != cites['cited_patent_assignee']] # filter out cites by same firm
cites.index = cites['citing_patent']
statefilter =  ((cites['citing_patent_state'] != cites['cited_patent_state']) \
               & ((cites['citing_patent_state'] == 'AK') | (cites['citing_patent_state'] == 'CA') | (cites['citing_patent_state'] == 'CT') | (cites['citing_patent_state'] == 'MN') \
               | (cites['citing_patent_state'] == 'MT') | (cites['citing_patent_state'] == 'ND') | (cites['citing_patent_state'] == 'NV') | (cites['citing_patent_state'] == 'OK') \
               | (cites['citing_patent_state'] == 'WA') | (cites['citing_patent_state'] == 'WV') | (cites['citing_patent_state'] == 'MI')))
cites_to_nonenforces = cites[statefilter]
cites_to_nonenforces = cites_to_nonenforces.drop_duplicates(cols=['citing_patent','nonenforce_patent'])
cites_to_nonenforces.to_csv('cites_to_nonenforces.csv',index=False,encoding='utf-8')
print len(cites_to_nonenforces), "citations to nonenforce patents"

"""
Need file like data.csv (so, joineddata_6monthwindow) but with each line just containing the most similar patent within the time window from a nonenforce state
"""
data = scoped_data
data['patent_x'] = data['patent_x'].apply(str)
data['patent_y'] = data['patent_y'].apply(str)
records = []
for michigan_patent in data['patent_x'].unique():
    tmp = data[(data['patent_x'] == michigan_patent) & (data['patent_y'] != michigan_patent)]
    if not tmp: continue
    index = tmp['similarity'].argmax()
    records.append(tmp.irow(index))
treatment_control_pairs = pd.DataFrame.from_records(records)
treatment_control_pairs.to_csv('out.csv',encoding='utf-8',index=False)

"""
Now need to generate the following file:
    <pair identifier>, <grant year of MI patent>, <cites to MI patent - cites to control patent in 1976>, <same for 1977>, etc etc <2013>

If no data exists, just output a "."
The pair identifier is MI patent number + control state + control patent

('patent_x','grant_date_x','application_date_x','assignee_x','number_inventors_x','state_x','similarity','patent_y','grant_date_y','application_date_y','assignee_y','number_inventors_y','state_y')

this uses treatment_control_pairs, cites_to_michigan, cites_to_nonenforces
"""
data = treatment_control_pairs[treatment_control_pairs['state_y'] != 'MI']
out = pd.DataFrame(data,columns=['patent_x','state_y','patent_y','similarity'])
out['pair identifier'] = out.apply(lambda row: row['patent_x'] + '_' + row['state_y'] + '_' + row['patent_y'], axis=1)
out['michigan_patent'] = out['patent_x']
cites_to_michigan = cites_to_michigan.fillna(datetime(1,1,1))
cites_to_nonenforces = cites_to_nonenforces.fillna(datetime(1,1,1))
cites_to_michigan['citing_patent_grant_date'] = cites_to_michigan['citing_patent_grant_date'].apply(lambda x: int(x.year))
cites_to_nonenforces['citing_patent_grant_date'] = cites_to_nonenforces['citing_patent_grant_date'].apply(lambda x: int(x.year))
# for each year, for each row in `data`, get cites to that michigan patent minus cites to the corresponding nonenforce patent
data['patent_x'] = data['patent_x'].apply(str)
for year in range(1976,2014): # 1976 through 2013
    yeardata = []
    for row in data.iterrows():
        michigan_patent = row[1]['patent_x']
        michcites = len(cites_to_michigan[(cites_to_michigan['citing_patent_grant_date'] == year) & (cites_to_michigan['michigan_patent'] == row[1]['patent_x'])])
        nonencites = len(cites_to_nonenforces[(cites_to_nonenforces['citing_patent_grant_date'] == year) & (cites_to_nonenforces['nonenforce_patent'] == row[1]['patent_y'])])
        yeardata.append({'michigan_patent': michigan_patent, year: michcites - nonencites})
    tmp = pd.DataFrame.from_records(yeardata)
    out = pd.merge(out, tmp, on='michigan_patent')
del out['patent_x']
del out['state_y']
del out['patent_y']
del out['michigan_patent']
out.to_csv('yeardata.csv',index=False,encoding='utf-8')

yeardata_withnulls = out
records = []
for row in yeardata_withnulls.iterrows():
    grant_year = data.irow(row[0])['grant_date_x'].year
    prefix = row[1][:2]
    before = ['.'] * (grant_year - 1976 + 1)
    after = row[1][2:][(grant_year - 1976 + 1):]
    records.append(list(prefix) + list(before) + list(after))
withnulls = pd.DataFrame.from_records(records)
withnulls.to_csv('yeardata_withnulls.csv',index=False,encoding='utf-8')

plt.figure()
out.mean()[1:].plot()
out.mean()[1:].to_csv('means.csv',index=False)
plt.savefig('means.png')

plt.clf()
for row in out.iterrows():
    row[1][2:].plot()
plt.savefig('all.png')

response = []
predictor = []
for row in out.iterrows():
    grant_year_michigan = data.irow(row[0])['grant_date_x'].year
    resp_before = [0] * (grant_year_michigan - 1976 + 1)
    resp_after = row[1][2:][(grant_year_michigan - 1976 + 1):]
    response.extend(list(resp_before) + list(resp_after))
    pred_before = [0] * (grant_year_michigan - 1976)
    pred_after = [1] * (2014 - grant_year_michigan)
    predictor.extend(pred_before + pred_after)

plt.clf()
out.sum()[2:].plot()
plt.savefig('sum.png')

for i in range(1976,2014):
    out[i] = out[i].apply(abs)
plt.clf()
out.sum()[2:].plot()
plt.savefig('absolute_sum.png')

m = {'response': response, 'predictor': predictor}
import scipy.io
import os
os.remove('data.mat')
scipy.io.savemat('data.mat',m)

print "N (years) =",len(range(1976,2014))
print "D (panels) =",len(out)

"""
Now need to do descriptive stats to compare the treatment (Michigan) and control (nonenforce) sets.
Stuff like # inventors, full # of cites, etc

treatment - mpd (table = michigan)
control - spd (table = similar)
"""

# inventors per patent
inv_per_patent_michigan = session.execute("select patent_id, count(*) from rawinventor \
                                           right join michigan_filtered on michigan_filtered.number = rawinventor.patent_id \
                                           group by patent_id;").fetchall()
inv_per_patent_michigan = pd.DataFrame.from_records(inv_per_patent_michigan)
inv_per_patent_michigan.columns = ['patent','num_inventors']

print "Number of Inventors per Michigan Patent"
print "mean",inv_per_patent_michigan['num_inventors'].mean()
print "median",inv_per_patent_michigan['num_inventors'].median()
print "mode",mode(inv_per_patent_michigan['num_inventors'])[0][0]
print "std",inv_per_patent_michigan['num_inventors'].std()
print "max",inv_per_patent_michigan['num_inventors'].max()
print "min",inv_per_patent_michigan['num_inventors'].min()
print "count",inv_per_patent_michigan['num_inventors'].sum()
print

inv_per_patent_similar = session.execute("select patent_id, count(*) from rawinventor \
                                           right join nonenforce on nonenforce.number = rawinventor.patent_id \
                                           group by patent_id;").fetchall()
inv_per_patent_similar = pd.DataFrame.from_records(inv_per_patent_similar)
inv_per_patent_similar.columns = ['patent', 'num_inventors']

print "Number of Inventors per nonenforce Patent"
print "mean",inv_per_patent_similar['num_inventors'].mean()
print "median",inv_per_patent_similar['num_inventors'].median()
print "mode",mode(inv_per_patent_similar['num_inventors'])[0][0]
print "std",inv_per_patent_similar['num_inventors'].std()
print "max",inv_per_patent_similar['num_inventors'].max()
print "min",inv_per_patent_similar['num_inventors'].min()
print "count",inv_per_patent_similar['num_inventors'].sum()
print

# citations per patent
all_cites_to_michigan = session.execute("select michigan_filtered.number, YEAR(patent.date), 1 from uspatentcitation \
                                         right join michigan_filtered on michigan_filtered.number = uspatentcitation.citation_id \
                                         left join patent on patent.id = uspatentcitation.patent_id;").fetchall()
all_cites_to_michigan = pd.DataFrame.from_records(all_cites_to_michigan)
all_cites_to_michigan.columns = ['number','year', 'count']

print "Number of pre1985 Forward Citations to Michigan"
tmp = all_cites_to_michigan[all_cites_to_michigan['year'] < 1985]
tmp = tmp.groupby('number').size()
print "mean",tmp.mean()
print "median",tmp.median()
print "mode",mode(tmp)[0][0]
print "std",tmp.std()
print "max",tmp.max()
print "min",tmp.min()
print "count",tmp.sum()
print

print "Number of post1985 Forward Citations to Michigan"
tmp = all_cites_to_michigan[all_cites_to_michigan['year'] > 1985]
tmp = tmp.groupby('number').size()
print "mean",tmp.mean()
print "median",tmp.median()
print "mode",mode(tmp)[0][0]
print "std",tmp.std()
print "max",tmp.max()
print "min",tmp.min()
print "count",tmp.sum()
print

all_cites_to_nonenforce = session.execute("select nonenforce.number, YEAR(patent.date), 1 from uspatentcitation \
                                         right join nonenforce on nonenforce.number = uspatentcitation.citation_id \
                                         left join patent on patent.id = uspatentcitation.patent_id;").fetchall()
all_cites_to_nonenforce = pd.DataFrame.from_records(all_cites_to_nonenforce)
all_cites_to_nonenforce.columns = ['number','year','count']

print "Number of pre1985 Forward Citations to Nonenforce"
tmp = all_cites_to_nonenforce[all_cites_to_nonenforce['year'] < 1985]
tmp = tmp.groupby('number').size()
print "mean",tmp.mean()
print "median",tmp.median()
print "mode",mode(tmp)[0][0]
print "std",tmp.std()
print "max",tmp.max()
print "min",tmp.min()
print "count",tmp.sum()
print

print "Number of post1985 Forward Citations to Nonenforce"
tmp = all_cites_to_nonenforce[all_cites_to_michigan['year'] > 1985]
tmp = tmp.groupby('number').size()
print "mean",tmp.mean()
print "median",tmp.median()
print "mode",mode(tmp)[0][0]
print "std",tmp.std()
print "max",tmp.max()
print "min",tmp.min()
print "count",tmp.sum()
print


# clean up database
session.execute('drop table michigan;')
session.execute('drop table similar;')
session.execute('drop table michigan_filtered;')
session.execute('drop table nonenforce;')

## play with results
#import IPython
#IPython.embed(user_ns=locals())
