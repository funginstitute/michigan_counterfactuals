import pandas as pd
import matplotlib.pyplot as plt

means = pd.read_csv('means.csv',header=None)
coefs = pd.read_csv('coefficients.csv',header=None)

plt.plot(range(1976,2014),means, label='means')
plt.plot(range(1976,2014),coefs[:-1], label='coefficients')
plt.legend(('means','coefficients'))
plt.savefig('coefficients_and_means.png')
