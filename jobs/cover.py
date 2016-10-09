from __future__ import division
from ..algo.util import *
from ..algo.peer_assignment import *
from grading import *
from math import sqrt
from peermatchflow import insert_ta_matches_from_accessor


####
# calculates the list of submissions that are insufficiently reviewed.
# input:
#     reviews: {i: {j: s, ...}, ...}
#     truths: {j:s,...}
#     required: minimum number of required reviews
# output: 
#     [submission,...]
#
def insufficiently_reviewed(reviews,truths,required=2):
    graded = truths.keys() # submissions that have a TA assigned.
    unsufficiently = insufficiently_peer_reviewed(reviews)

    return list(set(unsufficiently) - set(graded))

# this does not take current TA assignments (that are not graded) into account.
def insufficiently_peer_reviewed(reviews,required=2):
    jis = kkv_invert(ensure_kkv(reviews))
    
    need_to_grade = [j for j,itos in jis.items() if len([s for s in itos.values() if isinstance(s,Number)]) < required]
    
    # if the submissions are tuples, i.e., (j=submission,q=rubric_question) 
    # then strip the question and just output a list of submissions.  
    if need_to_grade and isinstance(need_to_grade[0],tuple):
        need_to_grade = [jq[0] for jq in need_to_grade]
        
    return list(set(need_to_grade))
    

# list submissions for which there are insufficient number of reviews.
# returns: [submission,...]
#
def insufficiently_reviewed_from_accessor(accessor, assignmentID, required = 2, courseID = None):

    reviews = reviews_from_accessor(accessor,assignmentID,courseID)
    tas = tas_from_accessor(accessor,courseID)
    
    truths = truths_from_reviews(reviews,tas)
    peer_reviews = reviews_filter_peers(reviews,tas)
    
#    pprint(stats(peer_reviews,truths))
    
    return insufficiently_reviewed(reviews,truths,required)
    
    

def insert_ta_matches_for_insufficiently_reviewed(accessor,assignmentID,courseID=None,required=2):
    subs = insufficiently_reviewed_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID,required=required)
    subs = [int(s) for s in subs]
    
    
    if not subs:
        logger.info("all submissions are sufficiently reviewed, no additional TA reviews are needed.")
        return []
    
    logger.info("found %s submissions that have been insufficiently reviewed: %s",len(subs),subs)
    
    insert_ta_matches(accessor,assignmentID,subs)
    subs = insufficiently_reviewed_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID,required=required)

    if not subs:
        logger.info("assigned TAs to review all insufficiently reviewed submissions.")
    else:
        logger.warn("assigned TAs to review, but still need to review %s",subs)
    
    return subs


def check_cover(reviews,truths):
    reviews = ensure_tuples(reviews)

    # [(i,j),...]
    matches = reviews_to_matches(reviews)

    # {i:js,...}
    assignment = pairs_to_kvs(matches)

    cover = truths_to_cover(truths)

    return cover_check(assignment,cover)


def submission_priority_for_cover(variance,degree):
    if variance < 0.5:
        return degree/2
    else:
        return degree*sqrt(variance)


#
def ensure_cover_from_accessor(accessor, assignmentID, courseID = None,priority=submission_priority_for_cover):
    reviews = reviews_from_accessor(accessor,assignmentID,courseID)
    truths = truths_from_accessor(accessor,assignmentID,courseID)
    weights = accessor.get_rubric_weights(assignmentID)

    return ensure_cover(reviews,truths,weights,priority)




# given reviews and truths, return submissions needed to be covered 
# runs vancouver to prioritize by variance.
#    reviews: {i:{(j,q):score,...},...}
#    truths: {(j,q):score,...}
#    weights: {q:weight,...}
#    priority: variance,degree -> priority (higher is better)
#    require: [j,...] submissions required to be in the cover.
def ensure_cover(reviews,truths, weights={},priority=submission_priority_for_cover,require=[]):

    assignment = ensure_kvs(reviews_to_matches(reviews))
    original_cover = truths_to_cover(truths)

    # the submissions that are required that are not already in the cover.
    require = list(set(require) - set(original_cover))

    if require:
        logger.warn("requiring submissions %s in the cover",require)

    ##
    ## find peers that need to be covered 
    ##
    check = cover_check(assignment,original_cover + require)


    # we already have a cover, return the residual in 'require'.
    if 0 not in check:
        logger.warn("no additional submissions needed in cover")
        return require

    # uncovered submissions
    uncovered = check[0]

    logger.warn("found %d uncovered reviewers",len(uncovered))


    # nothing to cover, return empty list
    if not uncovered:
        return []

    ##
    ## run vancouver to prioritize submissions.
    ##

    # set default weight to 1.0 (only if weights = {})
    def weight(q):
        return weights.get(q,1.0)

    # run vancouver and to prioritize based on variance.
    if vancouver_preconditions(reviews,truths):

        logger.warn("running vancouver to get priorities for greedy cover algorithm")
        
        (rrr,ttt) = prepare_for_vancouver(reviews,truths)

        (scores,_) = vancouver(rrr,ttt,10)


        vars = [(j,var*weight(q)) for ((j,q),(_,var)) in scores.items()]

        
        jvs = pairs_to_kvs(vars)
    
        # we should do a weighted sum here, but we don't have weights.
        variance = {j:sum(vs) for j,vs in jvs.items()}

    else:
        variance = {}

    # default variance. (only if variance = {})
    def var(j):
        return variance.get(j,1.0)



    ##
    ## 
    ## 
    def p(j,d):
        return priority(var(j),d)
    cover = greedy_cover(assignment,uncovered,p)

    if duplicates(original_cover+cover):
        logger.error("DUPLICATES IN COVER: this should not be happening")

    check = cover_check(assignment, list(set(original_cover+cover+require)))
    if 0 in check:
        logger.error("FAILED TO COVER PEERS %s: this should not be happening",check[0])

    logger.warn("given reviews, need %d submissions in cover",len(cover)+len(require))
    return [int(j) for j in cover] + [int(j) for j in require]



def reoptimize_cover_from_accessor(accessor, assignmentID, courseID = None,priority=submission_priority_for_cover):
    reviews = reviews_from_accessor(accessor,assignmentID,courseID)
    truths = truths_from_accessor(accessor,assignmentID,courseID)
    weights = accessor.get_rubric_weights(assignmentID)
    tas = tas_from_accessor(accessor,courseID)

    return reoptimize_cover(reviews,truths,tas,weights,priority)

# REOPTIMIZE_COVER
# Input:
#    reviews: {i:{j,score,...},...}
#    returns: {j:score,...}
#    tas: [i,...]
#    require: [j,...] submissions required to be in the cover.
# Output:
#    cover
def reoptimize_cover(reviews, truths, tas, weights={}, priority=submission_priority_for_cover,require=[]):
    
    # reviewed_truths: {(j,q):score,...}
    reviewed_truths = {j:score for j,score in truths.items() if isinstance(score,Number)}
    
    # unreviewed: [j,...]
    unreviewed = list(set([int(first(j)) for j,score in truths.items() if not isinstance(score,Number)]))
    
    # cover: [j,...]
    cover = ensure_cover(reviews,reviewed_truths,weights=weights,priority=priority,require=require)
    
    # add: cover \ unreviewed
    # remove: unreviewed \ cover
    # keep: cover intersect unreviewed.
    add = list(set(cover) - set(unreviewed))
    remove = list(set(unreviewed) - set(cover))


    return (add,remove)
    

def reoptimize_cover_execute(accessor, assignmentID, courseID = None,priority=submission_priority_for_cover,required=2):
    mechta_reviews = mechta_reviews_from_accessor(accessor,assignmentID,courseID)
    reviews = mechta_reviews_to_reviews(mechta_reviews)
    truths = truths_from_accessor(accessor,assignmentID,courseID)
    weights = accessor.get_rubric_weights(assignmentID)
    tas = tas_from_accessor(accessor,courseID)

    # submissions with insufficient reviews are required to be in the cover.
    require = insufficiently_peer_reviewed(reviews,required)

    (add,remove) = reoptimize_cover(reviews,truths,tas,weights,priority,require)
    
    logger.warn("adding %d submissions to original cover, removing %d submissions",len(add),len(remove))

    # [(i,j,matchID),...]
    matchids = mechta_reviews_to_matchids(mechta_reviews)
    ta_matchids = reviews_filter_tas(matchids,tas)


    remove_matchids = [int(id) for (_,j,id) in ta_matchids if int(j) in remove]
    
    ## remove matchids
    logger.warn("calling DELETE_MATCH_BULK on %s",remove_matchids)
    accessor.peermatch_delete_match_bulk(remove_matchids)

    ## assign new ta reviews.
    logger.warn("calling INSERT_TA_MATCHES on %s",add)
    insert_ta_matches_from_accessor(accessor,assignmentID,add)

    return True
