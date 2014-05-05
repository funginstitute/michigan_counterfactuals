import pandas as pd

t = pd.read_csv('treatmentdates.csv')
c = pd.read_csv('controldates.csv')

t.date = t.date.apply(pd.to_datetime)
c.date = c.date.apply(pd.to_datetime)

data = []
x = c.loc[10].date - t.loc[10].date

for row in t.iterrows():
  diffs = pd.to_timedelta(abs(c.date - row[1]['date']))
#  print dir(diffs)
#  print diffs
#  print diffs.loc[0] / pd.np.timedelta64(1,'D')
#  print diffs.loc[0].days
#  print diffs.days
#  print '-'*10
  closeenough = c[diffs / pd.np.timedelta64(1,'D') < 185]# / pd.np.timedelta64(1, 'D') < 185]
  for cr in closeenough.iterrows():
    print row[1]['id'], cr[1]['id']

