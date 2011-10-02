# -*- coding: utf-8 -*-
"""
    bdd.py

    An advanced Binary Decision Diagram library for Python

    :copyright: (c) 2011 by Christian Hans
"""

from math import log
from inspect import getargspec
from sys import getsizeof

class BDD(object):
    n = 0
    root = None

    # TODO: move to __init__
    _vcount = 0

    def __init__(self, function=None, values=None, reduce=True):

        def generate_tree_function(function, path=[]):
            path_len = len(path)
            if path_len<self.n:
                v = Vertex(index=path_len+1)
                v.low = generate_tree_function(function, path+[False])
                v.high = generate_tree_function(function, path+[True])
                return v
            elif path_len==self.n:
                # reached leafes
                return Vertex(value=function(*path))

        def generate_tree_values(values, level=0):
            if level<self.n:
                v = Vertex(index=level+1)
                v.low = generate_tree_values(values, level+1)
                v.high = generate_tree_values(values, level+1)
                return v
            elif level==self.n:
                # reached leafes
                v = Vertex(value=values[self._vcount])
                self._vcount = self._vcount + 1
                return v

        if function:
            self.n = len(getargspec(function).args)
            self.root = generate_tree_function(function)
            if reduce:
                self.reduce()
        elif values:
            values_count = len(values)

            if values_count%2!=0:
                raise ValueError('Number of values must be a power of 2')
            else:
                self.n = int(log(values_count, 2))
                self._vcount = 0
                self.root = generate_tree_values(values)
                if reduce:
                    self.reduce()

    def eval(self, *args):
        def _eval(v, *args):
            if v.index!=None:
                if not args[v.index-1]:
                    return _eval(v.low, *args)
                else:
                    return _eval(v.high, *args)
            elif v.value!=None:
                return v.value

        if len(args)!=self.n:
            raise TypeError('BDD takes exactly ' + str(self.n) +
                ' arguments (' + str(len(args)) + ' given)')

        return _eval(self.root, *args)

    def traverse(self):
        def _traverse(v, levels):
            if v.index!=None:
                levels[v.index-1].append(v)
                _traverse(v.low, levels)
                _traverse(v.high, levels)
            elif v.value!=None:
                levels[len(levels)-1].append(v)

        levels = []
        for i in xrange(self.n+1):
            levels.append([])
        _traverse(self.root, levels)
        return levels

    def reduce(self):
        result = []
        nextid = 0

        # Traverse tree, so that level[i] contains all vertices of level i
        levels = self.traverse()
        levels.reverse()

        # Bottom-up iteration over the BDD
        for level in levels:
            iso_map = {}

            # Merge isomorphic vertices in this tree level under same key in iso_map
            for v in level:
                # Generate key
                if v.value!=None:
                    key = str(v.value)
                elif v.low.id==v.high.id:
                    v.id = v.low.id
                    continue
                else:
                    key = str(v.low.id) + ' ' + str(v.high.id)

                # Append under key to iso_map
                if key in iso_map:
                    iso_map[key].append(v)
                else:
                    iso_map[key] = [v]

            for key, vertices in iso_map.items():
                # Set same id for isomorphic vertices
                for v in vertices:
                    v.id = nextid
                nextid = nextid + 1

                # Store one isomorphic vertex in result
                x = vertices[0]
                result.append(x)

                # Update references
                if x.index!=None:
                    x.low = result[x.low.id]
                    x.high = result[x.high.id]

        # Update reference to root vertex (alwayes the last entry in result)
        self.root = result[-1]

    def apply(self, bdd, function):
        cache = {}

        def _apply(v1, v2, f):
            # Check if v1 and v2 have already been calculated
            key = str(v1.id) + ' ' + str(v2.id)
            if key in cache:
                return cache[key]

            u = Vertex()
            cache[key] = u

            if v1.value!=None and v2.value!=None:
                u.value = f(v1.value, v2.value)
            else:
                if v1.index!=None and (v2.value!=None or v1.index<v2.index):
                    u.index = v1.index
                    u.low = _apply(v1.low, v2, f)
                    u.high = _apply(v1.high, v2, f)
                elif v1.value!=None or v1.index>v2.index:
                    u.index = v2.index
                    u.low = _apply(v1, v2.low, f)
                    u.high = _apply(v1, v2.high, f)
                else:
                    u.index = v1.index
                    u.low = _apply(v1.low, v2.low, f)
                    u.high = _apply(v1.high, v2.high, f)

            return u

        new_bdd = BDD()
        new_bdd.n = self.n
        new_bdd.root = _apply(self.root, bdd.root, function)
        new_bdd.reduce()
        return new_bdd

    # Returns True if the BDD represents function
    def represents(self, function):
        def _represents(args=[]):
            args_len = len(args)
            if args_len==self.n:
                return function(*args)==self.eval(*args)
            elif args_len<self.n:
                return _represents(args+[False]) and _represents(args+[True])

        if len(getargspec(function).args)==self.n:
            return _represents()
        else:
            return False

    def __eq__(self, other):
        def equal(x1, x2):
            return x1==x2

        return (isinstance(other, BDD) and
            self.apply(other, equal).root == Vertex(value=True))

    def __len__(self):
        def _count_bdd(v):
            if v.index!=None:
                return 1 + _count_bdd(v.low) + _count_bdd(v.high)
            elif v.value!=None:
                return 1
        return _count_bdd(self.root)

    def __sizeof__(self):
        def _sizeof_bdd(v):
            if v.index!=None:
                return getsizeof(v) + _sizeof_bdd(v.low) + _sizeof_bdd(v.high)
            elif v.value!=None:
                return getsizeof(v)
        return _sizeof_bdd(self.root)

    def __repr__(self):
        def _bdd_to_string(v):
            if v.index!=None:
                return v.__repr__() + '\n' + _bdd_to_string(v.low) + '\n' + _bdd_to_string(v.high)
            elif v.value!=None:
                return v.__repr__()
        return '<BDD n=' + str(self.n) + ',\n' + _bdd_to_string(self.root) + '>'

class Vertex(object):
    id = None
    index = None
    value = None
    low = None
    high = None

    def __init__(self, index=None, value=None, low=None, high=None):
        self.index = index
        self.value = value
        self.low = low
        self.high = high

    def __eq__(self, other):
        if self.index!=None and other.index!=None:
            return self.index==other.index
        elif self.value!=None and other.value!=None:
            return self.value==other.value
        else:
            return False

    def __repr__(self):
        if self.index!=None:
            return '<Vertex ' + str(self.index) + '>'
        elif self.value!=None:
            return '<Vertex ' + str(self.value) + '>'
        else:
            return '<Vertex>'
