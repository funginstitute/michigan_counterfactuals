import pandas as pd

def trim_fraction(text):
    if '.0' in text:
        return text[:text.rfind('.0')]
    return text

cites = pd.read_csv('cites_to_control.tsv',delimiter='\t')
cites['cited'] = cites['cited'].astype(str).apply(trim_fraction)
cites['citing'] = cites['citing'].astype(str).apply(trim_fraction)

x = cites.copy()
for y in range(1975,2014):
    x[y] = 0

del x['citing']
del x['citing_year']
x = x.drop_duplicates('cited')
x = x.set_index(x['cited'])

for y in range(1975,2014):
    d = cites[cites['citing_year'] == y].groupby('cited').count()
    if d:
        x[y] = d['cited'].astype(str).apply(trim_fraction)
        x[y] = x[y].fillna(0)

    #import IPython
    #IPython.embed(user_ns = locals())
x.to_csv('citestocontrolbyyear.csv',index=False)
