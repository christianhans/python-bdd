# -*- coding: utf-8 -*-

# This script calculates the reduce algorithm's compression ratio
# for different n values.

from bdd import BDD
from random import choice

count = 100
result = []

for k in xrange(10):
    n = k+1
    avg = 0.0

    # Calculate average size of count BDDs
    for i in xrange(count):
        size = len(BDD(values=[choice([True, False]) for j in xrange(2**n)]))

        # Weighted average value
        avg = (float(i)/(i+1))*avg + (1.0/(i+1))*size

    ratio = avg/(2**(n+1)-1)
    result.append(ratio)
    print 'n=' + str(n) + ': ' + str(ratio*100) + '%'
