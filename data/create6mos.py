import pandas as pd

t = pd.read_csv('treatmentdates',delimiter='\t')
c = pd.read_csv('controldates',delimiter='\t')

t.date = t.date.apply(pd.to_datetime)
c.date = c.date.apply(pd.to_datetime)

data = []

for row in t.iterrows():
  closeenough = c[abs(c.date - row[1].date).astype('timedelta64[D]') < 185]# / pd.np.timedelta64(1, 'D') < 185]
  for cr in closeenough.iterrows():
    print row[1]['id'], cr[1]['id']
    data.append((row[1]['id'], cr[1]['id']))

