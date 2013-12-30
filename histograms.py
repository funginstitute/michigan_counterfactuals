"""
Looks at michigandistances.csv, which is of schema

michigan patent,similar patent,similarity score

and plots a histogram of distances. If no command line
argument is provided, then the histogram is of all distances.
Any and all arguments should be michigan patent numbers,
and individual histograms will be plotted for each of them.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

michigandistances = pd.read_csv('michigandistances.csv')
michigandistances['michigan'] = michigandistances['michigan'].apply(str)
michigandistances['similar'] = michigandistances['similar'].apply(str)
michigandistances = michigandistances[michigandistances['michigan'] != michigandistances['similar']]


def plot(*numbers):
    if not numbers:
        michigandistances['similarity'].hist(bins=8,range=(0.2,1.0))
        plt.savefig('histogram.png')
    else:
        for number in numbers:
            print number
            plt.clf()
            tmp = michigandistances[michigandistances['michigan'] == number]
            empty = {'michigan': [number], 'similar': [number], 'similarity': [1.0]}
            tmp = pd.concat((tmp, pd.DataFrame.from_dict(empty)))
            tmp['similarity'].hist(bins=8,range=(0.2,1.0))
            plt.savefig('{0}_histogram.png'.format(number))

if __name__=='__main__':
    plot(*sys.argv[1:])
