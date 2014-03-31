import pandas as pd
import sys
import random

d = pd.read_csv(sys.argv[1])
num = sys.argv[2]

rows = random.sample(d.index, int(num))

d.ix[rows].to_csv('sample.csv',index=False,header=None)
