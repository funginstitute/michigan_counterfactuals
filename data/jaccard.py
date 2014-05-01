import sys
from io import StringIO
from itertools import islice

"""
Helpful object for distance measures. Initialize with a [filename] that is a path to a file
of schema:
    id number,space separated list of tags
Use as you can see in run_distance_computation
"""
class Dataset(object):
    def __init__(self, filename):
        self.data = {}
        self.tags = set()
        for line in open(filename):
            line = line.strip()
            num = line.split(',')[0]
            tags = set(line.split(',')[1].split(' '))
            self.data[num] = tags
            self.tags.update(tags)
        print("Initialized dataset with {0} unique tags and {1} data points".format(len(self.tags), len(self.data)))

    def __iter__(self):
        for k,v in self.data.items():
            yield (k,v)
    
    def __getitem__(self, key):
        iterator = enumerate(self.data.items())
        n = key.start
        next(islice(iterator, n, n), None)
        for i,(k,v) in iterator:
            yield (k,v)

def jaccard_distance(tags1, tags2):
    """
    returns the jaccard index for two Sets of tags
    """
    return len(tags1.intersection(tags2)) / len(tags1.union(tags2))

def run_distance_computation(distance_fxn, ds1, ignore_zero=False, outfile=None):
    """
    Using a [distance_fxn], computes pairwise distances among all records in [ds1].
    If [ignore_zero] is True, then only nonzero distances will be output
    If [outfile] is nonnull, then a file will be created with the same name as the
      string [outfile] and the distances will be deposited there
    """
    if outfile:
        f = open(outfile,'wb')
    for i, (num1, tags1) in enumerate(ds1):
        for num2, tags2 in ds1[i:]:
            if num1 == num2: continue # ignore unnecessary 1.0
            dist = distance_fxn(tags1, tags2)
            if ignore_zero:
                if not dist: continue
            s = '{0},{1},{2}\n'.format(num1,num2,dist)
            if outfile:
                f.write(s)
            else:
                print(s),

def run_distance_computation_external(distance_fxn, ds1, ds2, ignore_zero=False, outfile=None):
    """
    Using a [distance_fxn], computes pairwise distances for all records in [ds1] against [ds2]
    If [ignore_zero] is True, then only nonzero distances will be output
    If [outfile] is nonnull, then a file will be created with the same name as the
      string [outfile] and the distances will be deposited there
    """
    if outfile:
        f = open(outfile,'wb')
    for num1, tags1 in ds1:
        for num2, tags2 in ds2:
            if num1 == num2: continue # ignore unnecessary 1.0
            dist = distance_fxn(tags1, tags2)
            if ignore_zero:
                if not dist: continue
            s = '{0},{1},{2}\n'.format(num1,num2,dist)
            if outfile:
                f.write(s)
            else:
                print(s),


### Configuration Options ***
IGNORE_ZERO = True # True or False
OUTFILE = 'michigandistances.csv' # None or some filename string
DISTANCE_MEASURE = jaccard_distance # this is a function name

if __name__=='__main__':
    if len(sys.argv) == 2:
        d_filename = sys.argv[1]
        d = Dataset(d_filename)
        run_distance_computation(DISTANCE_MEASURE, d, ignore_zero = IGNORE_ZERO, outfile=OUTFILE)
    elif len(sys.argv) == 3:
        d_filenamefilename = sys.argv[1]
        d = Dataset(d_filenamefilename)
        src_filename = sys.argv[2]
        src = Dataset(src_filename) 
        run_distance_computation_external(DISTANCE_MEASURE, d, src, ignore_zero = IGNORE_ZERO, outfile=OUTFILE)
    else:
        print("""
Usage:
    python vincent.py <filename> -- computes pairwise distances
      among all tag lines in this one file
    python vincent.py <filename1> <filename2> -- computes pairwise
      distances for every line in filename1 against every line in
      filename2
""")
