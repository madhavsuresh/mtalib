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

# input: [(i,j,v),...]
# output: {i => j => v,...}
def tuples_to_kkv(tuples):
    i_s = set([i for (i,_,_) in tuples])
    
    kkv = {i:{} for i in i_s}
    
    for i,j,v in tuples:
        kkv[i][j] = v
        
    return kkv

# input: {i => j => v,...}
# output: {j => i => v,...}
def kkv_invert(kkv):
    tuples = kkv_to_tuples(kkv)
    
    return tuples_to_kkv([(j,i,v) for (i,j,v) in tuples])   
