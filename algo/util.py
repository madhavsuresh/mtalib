from __future__ import division


# invert a dictionary of lists (assuming no duplicates)
def invert_dictlist(d):
    return dict( (v,k) for k in d for v in d[k] )

# invert a dictionary of lists (with duplicates)
def invert_dictlist_dup(d):
    values = set(a for b in d.values() for a in b)
    reverse_d = dict((new_key, [key for key,value in d.items() if new_key in value]) for new_key in values)
    return reverse_d

#note this will only work on hashable objects
def duplicates(tocheck):
  return len(tocheck) != len(set(tocheck))

# return the average of the numbers in the list.
def avg(lst):
    return sum(lst)/len(lst) if len(lst) > 0 else 0.0

# input: {i => j => v,...}
# output: [(i,j,v),...]
def kkv_to_tuples(kkv):
    return [(i,j,v) for (i,jtov) in kkv.items() for j,v in jtov.items()]

def pairs_to_kvs(pairs):
    tuples = [(i,j,None) for i,j in pairs]
    
    kkv = tuples_to_kkv(tuples)

    kvs = {i : jtov.keys() for i,jtov in kkv.items()}
    return kvs

def kvs_to_pairs(kvs):
    pairs = [(i,j) for i,vs in kvs.items() for j in vs]
    return pairs

def kvs_invert(kvs):
    pairs = [(j,i) for (i,j) in kvs_to_pairs(kvs)]
    return pairs_to_kvs(pairs)

def ensure_kvs(kvs):
    return kvs if isinstance(kvs,dict) else pairs_to_kvs(kvs)

# input: [(i,j,v),...]
# output: {i => j => v,...}
def tuples_to_kkv(tuples):
    i_s = set([i for (i,_,_) in tuples])
    
    kkv = {i:{} for i in i_s}
    
    for i,j,v in tuples:
        kkv[i][j] = v
        
    return kkv



def ensure_tuples(kkv_or_tuples):
    return kkv_to_tuples(kkv_or_tuples) if isinstance(kkv_or_tuples,dict) else kkv_or_tuples

def ensure_kkv(kkv_or_tuples):
    return kkv_or_tuples if isinstance(kkv_or_tuples,dict) else tuples_to_kkv(kkv_or_tuples)


# input: {i => j => v,...}
# output: {j => i => v,...}
def kkv_invert(kkv):
    tuples = ensure_tuples(kkv)
    
    return tuples_to_kkv([(j,i,v) for (i,j,v) in tuples])   

# input: {i => j => v,...}
# output: {(i,j) => v,...}
def kkv_to_kv(kkv):
    return {(i,j):v for i,jv in ensure_kkv(kkv).items() for j,v in jv.items()}
