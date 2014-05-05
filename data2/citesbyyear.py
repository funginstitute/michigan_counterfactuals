import pandas as pd

def trim_fraction(text):
    if '.0' in text:
        return text[:text.rfind('.0')]
    return text

cites = pd.read_csv('cites_to_treatment.tsv',delimiter='\t')
#control = pd.read_csv('control.csv',header=None)
#control[1] = control[1].astype(str).apply(trim_fraction)
cites['cited'] = cites['cited'].astype(str).apply(trim_fraction)
cites['citing'] = cites['citing'].astype(str).apply(trim_fraction)
#merged = pd.merge(control,cites,left_on=1,right_on='cited')
#merged = merged[merged[0] != merged['state']]
#cites = merged[['citing','cited','citing_year']]
cites = cites.drop_duplicates(cols=['cited','citing'])

x = cites.copy()
for y in range(1975,2014):
    x[y] = 0

del x['citing']
del x['citing_year']
x = x.drop_duplicates('cited')
x = x.set_index(x['cited'])

for y in range(1975,2014):
    d = cites[cites['citing_year'] == y].groupby('cited').count()
    if len(d):
        x[y] = d['cited'].astype(str).apply(trim_fraction)
        x[y] = x[y].fillna(0)

    #import IPython
    #IPython.embed(user_ns = locals())
#x.to_csv('citestocontrolbyyear.csv',index=False)
x.to_csv('citestotreatmentbyyear.csv',index=False)
