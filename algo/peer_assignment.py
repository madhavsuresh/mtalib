from __future__ import division
import math 
import random
from util import *
from copy import copy,deepcopy

####
# GENERATE PEER ASSIGNMENT
# Input:
#    - peers: [peer ids]
#    - submissions: [submission ids].
#    - k: number of submissions to assign each peer.
#    - cover: [submission ids] (PASS BY REFERENCE)
#    - excludes: {peer id : [excluded submission ids]}
#    - num_tries: attempts a random matching this many times
#         (fails and returns {} if num_tries is exceeded)
# Output:
#    - assignments: {peer id : [submission_ids]} 
#
# Notes:
#    - if 'cover' is [], then it will replace with a random cover.
#      (pass by reference)
def peer_assignment_covered(peers,submissions,k,cover=[],excludes={},num_tries=1000):
    
    m = len(submissions)
    n = len(peers)

    excludes = {p : (excludes[p] if p in excludes else []) for p in peers}
    
    # load = ceil(n * k / m)
    # this is how many copies of random submission lists we need.
    load = int(math.ceil((n * k) / m))

    # extend cover to be the right length 
    # by adding random elements from 'submissions \ cover'
    cover_len = math.ceil(n/load)
    if len(cover) < cover_len:
        # get random elements from 'submissions \ cover'
        gen_cover = random.sample(set(submissions).difference(set(cover)),int(math.ceil(n/load)))
        # add to cover.
        cover.extend(gen_cover) 


    # assign the agents to the cover. 
    cover_assignments = peer_assignment(peers,cover,1,excludes,num_tries)
    if not cover_assignments:
        return {}


    # add cover_assignment to excludes.
    excludes = {p: excludes[p] + cover_assignments[p] for p in peers}

    # the remaining submissions
    residual_submissions = list(set(submissions).difference(set(cover)))

    residual_assignments = peer_assignment(peers,residual_submissions,k-1,excludes,num_tries)
    if not residual_assignments:
        return {}
    
    # combine cover and residual assignment
    assignments = {p: cover_assignments[p] + residual_assignments[p] for p in peers}

    return assignments
    
####
# GENERATE PEER ASSIGNMENT
# Input:
#    - peers: [peer ids]
#    - submissions: [submission ids].
#    - k: number of submissions to assign each peer.
#    - excludes: {peer id : [excluded submission ids]}
#    - num_tries: attempts a random matching this many times
#         (fails and returns {} if num_tries is exceeded)
# Output:
#    - assignments: {peer id : [submission_ids]} 
def peer_assignment(peers,submissions,k,excludes={},num_tries=1000):
    n = len(peers)
    m = len(submissions)

    excludes = {p : (excludes[p] if p in excludes else []) for p in peers}


    # number of peers per submission (rounded down).
    load = (n * k) // m

    peer_reps = list(peers) * k
    submission_reps = submissions * load

    count = 0
    # try to get a matching with out duplicates or excluded assignments.
    for _ in range(num_tries):

        count += 1


        # add random extra submissions because submission_reps is rounded down.
        excess = random.sample(submissions,n*k - m*load)

        # shuffle.
        random.shuffle(peer_reps)

        # match.
        assignments = pairs_to_kvs(zip(peer_reps,submission_reps + excess))

        # check for duplicates or excluded assignemnts
        if any(duplicates(assignments[p] + excludes[p]) for p in peers):
            continue


        print "finished with " + str(count) + " tries."
        return assignments
 
    # we failed to find an assignment given the in num_tries tries.
    return {}



####
# CHECK TO SEE IF A PEER ASSIGNMENT IS VALID
#    - peers are not assigned to review the same submission multiple times.
#    - peers are not assigned to review any submissions in their excludes list.
def peer_assignment_check(peers,assignments,cover,excludes):
    excludes = {p : (excludes[p] if p in excludes else []) for p in peers}

    # fail if peers are assigned duplicate assignments, 
    # or assignments required to be excluded.
    if any(duplicates(assignments[p] + excludes[p]) for p in peers):
        return False

    # fail if any peers are uncovered.
    if 0 in check_cover(assignment,cover):
        return False

    return True

# returns {count:peers,...}
#    - count: number of times covered
#    - peers: list of peers covered that many times.
# Note:
#    - count = 0 implies that there are uncovered peers.
def cover_check(assignment,cover):

    covercounts = [(len([j for j in js if j in cover]),i) for i,js in assignment.items()]

    return pairs_to_kvs(covercounts)

# generates random reviews for assignments 
#    (assignments as returned from peer_assignments())
#   qualities: {i => number of draws from distribituion}
def random_reviews(assignments, qualities = {}):
    # fill in qualities if empty.
    # default quality is 1.
    qs = {i:1 for i in assignments.keys()}
    qs.update(qualities)
    
    return {i: {j: avg([random.random() for _ in range(qs[i])]) for j in js} for (i, js) in assignments.items()} 

# RANDOM_ASSIGNMENT: randomly match reviwers to submissions_to_cover.
#   Input: 
#     reviewers: [i,...]
#     submissions_to_cover: [j,...]
#   Output:
#     assignment: {i: [j,...], ...} 
# ALIAS: RANDOM_TA_ASSIGNMENTS (depricated)
def random_assignment(reviewers, submissions_to_cover):
    n = len(reviewers)
    m = len(submissions_to_cover)

    random.shuffle(reviewers)

    extended_reviewers = (reviewers * (m // n + 1))

    matches = [(i,j) for i,j in zip(extended_reviewers,submissions_to_cover)]

    return pairs_to_kvs(matches)
# ALIAS: RANDOM_TA_ASSIGNMENTS (depricated)
random_ta_assignment = random_assignment


#
# finds and returns a cover, greedy by priority
# Input:
#   assignment: {i:js,...} 
#      the assignment of peers to submissions.
#   uncovered: [i,...] 
#      list of peers that need to be covered.
#   priority: (j,degree)->weight (higher is better)
#      which submissions 
def greedy_cover(assignment,uncovered,priority):

    # get our own copy of uncovered because we modify it.
    uncovered = copy(uncovered)

    # remove peers that are not in uncovered.  
    # (use deepcopy because this function modifies the assignment as it runs)
    assignment = {i:copy(assignment[i]) for i in uncovered}
    
    # {j:reviewers,...]
    reviewers = kvs_invert(assignment)

    # define priority function 
    def p(j):
        return priority(j,len(reviewers[j]))

    # while there are uncovered reviewers: 
    #   1. FIND highest priority submission,
    #   2. ADD it to cover.
    #   3. REMOVE affected reviewers and ADJUST data structures.
    cover = []
    while uncovered:

        # FIND and ADD the "highest priority" submission to the cover
        j = max(reviewers.keys(),key=p)
        cover.append(j)


        # when we add j to the cover
        #    (a) REMOVE reviewers i of j that are covered. 
        #    (b) submissions jj those reviewers reviewed do not need to cover i
        # ADJUST modify uncovered/reviewers/assignment to reflect this.
        for i in reviewers[j]:
            uncovered.remove(i)
            
            for jj in assignment[i]: 
                if jj == j:
                    continue
                
                # remove i from reviewers list for jj.
                reviewers[jj].remove(i)
                
                # if jj has no more reviewers.
                if not reviewers[jj]:
                    del reviewers[jj]

            del assignment[i]

        del reviewers[j]

    return cover
