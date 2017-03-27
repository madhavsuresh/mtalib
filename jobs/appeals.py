from __future__ import division
from ..api import api
from ..algo.util import *
from pprint import pprint


def get_appeal_submissions(accessor,assignmentID):
    
    appeals = accessor.get_appeals()
    matches_for_assignment = accessor.peermatch_get(assignmentID)
    subs = {m['matchID']:m['submissionID'] for m in matches_for_assignment}
    
    return list(set([subs[a['matchID']] for a in appeals if a['matchID'] in subs]))

def get_appeals(accessor,assignmentID):
    
    appeals = accessor.get_appeals()
    matches_for_assignment = accessor.peermatch_get(assignmentID)
    subs = {m['matchID']:m['submissionID'] for m in matches_for_assignment}
    
    return [a for a in appeals if a['matchID'] in subs]


## 
## dynamic program for scheduling
##
def schedule_appeals(nbins, bundles):
        
    # OPT(j,size_1,...,size_k])
    #    = max_i size_i from scheduling j ... m
    #    = when current sizes are {size_i}
            
    
    bins = range(nbins)
    
    # a strict upper bound on the makespan is given by the greedy 2-approximation: AVG + MAX
    max_size = sum(bundles)//nbins + max(bundles) +1
    m = len(bundles)
    print "maximum size " + str(max_size)
    
    # all possible profiles of sizes.
    sizes = [()]
    for i in range(nbins):
        sizes = [size + (s,) for size in sizes for s in range(max_size+1)]
    
    
    # increment the ith coordinate of size by inc.
    def increment_size(size,i,inc):
        size_list = list(size)
        size_list[i] = min(size_list[i] + bundles[j], max_size)
        return tuple(size_list)

    # initialize memo table.
    memos = {(m,) + size:max(size) for size in sizes}

    # fill memo table
    for j in reversed(range(m)):
        for size in sizes:
            def size_if_i(i):
                return memos[(j+1,)+increment_size(size,i,bundles[j])]
        
            i = min(bins,key = size_if_i)
            memos[(j,) + size] = size_if_i(i)

    print "scheduled in " + str(memos[(0,) * (nbins + 1)])
    
    jobs = {i:[] for i in bins}
    # find optimal solution
    size = (0,) * nbins
    for j in range(m):
        def size_if_i(i):
            return memos[(j+1,)+increment_size(size,i,bundles[j])]
            
        i = min(bins,key = size_if_i)
        jobs[i].append(j)
        size = increment_size(size,i,bundles[j])
    
    print "final sizes: " + str(size)
    
    return jobs


        
        
