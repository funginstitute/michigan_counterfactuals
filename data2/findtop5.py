import pandas as pd

md = pd.read_csv('michigandistances.csv',header=None)
print 'loaded michigan'
p = pd.read_csv('6monthwindow',delimiter=' ',header=None)
print 'loaded window'

def trim_fraction(text):
  if '.0' in text:
    return text[:text.rfind('.0')]
  return text

#md[1] = md[1].astype(str).apply(trim_fraction)
#print 'trim 1'
#md[0] = md[0].astype(str).apply(trim_fraction)
#print 'trim 2'
#
#p[1] = p[1].astype(str).apply(trim_fraction)
#print 'trim 3'
#p[0] = p[0].astype(str).apply(trim_fraction)
#print 'trim 4'

merged = pd.merge(md,p,left_on=[0,1],right_on=[0,1])
print 'merged'

merged = merged.sort(2)
print 'sorted'
merged.groupby(0).head(5).to_csv('top5.csv',index=False)
