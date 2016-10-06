from ..api.api import *
from ..algo.review_grades import review_grade,review_grades,NonScore
from ..algo.vancouver import *
from ..algo.peer_review_util import *
from numbers import Number


import logging
logger = logging.getLogger('mtalib.jobs.grading')






def mechta_reviews_from_accessor(accessor,assignmentID,courseID=None,rewrites={None:NonScore.NO_ANSWER,'Skip':NonScore.SKIP}):

    return accessor.get_peerreview_scores(assignmentID, courseID, rewrites)

####
# convert peerreviews from MechTA to [(i,(j,q),s),...] format:
#    - i: peerID
#    - j: submissionID
#    - q: questionID (in the rubric)
#    - s: score.
#
def mechta_reviews_to_reviews(mechta_reviews,peer_key='reviewerID'):
    tuples = [(review[peer_key]['id'],(j,q),response['score']) 
                 for j,reviews in mechta_reviews.items()
                 for review in reviews
                 for q,response in review['answers'].items() if 'score' in response]
    return tuples

# gives [(i,j,match_id),...]
def mechta_reviews_to_matchids(mechta_reviews,id_key='matchID'):
    tuples = [(review['reviewerID']['id'],j,review[id_key]['id']) 
                 for j,reviews in mechta_reviews.items()
                 for review in reviews]
    return tuples





def reviews_from_accessor(accessor,assignmentID,courseID=None,rewrites={None:NonScore.NO_ANSWER,'Skip':NonScore.SKIP},peer_key='reviewerID'):
    
    return mechta_reviews_to_reviews(mechta_reviews_from_accessor(accessor,assignmentID,courseID,rewrites),peer_key)

def tas_from_accessor(accessor,courseID=None):
    if not courseID:
        courseID = accessor.courseID

    return accessor.get_tas_from_course(courseID)['taIDs']


def missing_truths_from_accessor(accessor,assignmentID,courseID=None):
    params = locals()
    reviews = reviews_from_accessor(**params)
    del params['assignmentID']
    tas = tas_from_accessor(**params)
    
    return missing_truths(reviews,tas)


# returns submissions with missing TA reviews.
def missing_truths(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    ta_tuples = reviews_filter_tas(tuples,tas)
   
    missing_pairs = [(i,j) for (i,j,s) in ta_tuples if not isinstance(s,Number)]

    if not missing_pairs:
        return {}
    
    # convert (j,q) submissions to j
    if isinstance(missing_pairs[0],tuple):
        missing_pairs = [(i,j) for (i,(j,q)) in missing_pairs]
    
    return pairs_to_kvs(missing_pairs)


#####
# convert peer review tuples from both TAs and peers 
#    tuples: [(i,jq,s),..] 
#    tas: [i,...]
# to the vancouver format:
#    reviews: {i:{jq:s,...},...}
#    truths: {js:s,...}
#
#    note: if all TA scores for a submission are NonScore.NO_ANSWER 
#          then NonScore.NO_ANSWER is the score returned.
def truths_from_reviews(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    ta_tuples = reviews_filter_tas(tuples,tas)
    

    missing = missing_truths(ta_tuples,tas)
    if missing:
        logger.warn("missing TA reviews by TAs %s for submissions %s",missing.keys(),[j for js in missing.values() for j in js])
    

    def avg_scores(scores):
        numeric_scores = [s for s in scores if isinstance(s,Number)]
        return avg(numeric_scores) if numeric_scores else NonScore.NO_ANSWER

    ta_kkv = tuples_to_kkv([(j,i,v) for (i,j,v) in ta_tuples])
    truths = {j:avg_scores(itov.values()) for j,itov in ta_kkv.items()}
    
    return truths

def reviews_filter_tas(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    filtered = [(i,jq,s) for (i,jq,s) in tuples if int(i) in tas]
    return filtered

def reviews_filter_peers(reviews,tas):
    tuples = ensure_tuples(reviews)

    filtered = [(i,jq,s) for (i,jq,s) in tuples if int(i) not in tas]
    return filtered



#
# returns: {submission: grade, ...}
#
def grade_assignment(accessor, assignmentID, courseID = None):

    if courseID == None:
        courseID = accessor.courseID
    
    reviews = reviews_from_accessor(accessor,assignmentID, courseID)
    tas = accessor.get_tas_from_course(courseID)['taIDs']
    weights = accessor.get_rubric_weights(assignmentID)
    
    # pull out and flatten the TA reviews.
    truths = truths_from_reviews(reviews,tas)
    
    # run vancouver
    grades = run_vancouver(reviews,truths,10)
    
    ###
    # reweight grades across rubric and sum.
    ###
    
    total_weight = sum(weights.values())
    # weight and flatten to tuple: [(j,q,weighted_score),...]
    weighted = {(j,q,score*weights[q]) for ((j,q),score) in grades.items()}
    # convert to kkv:              {j:{q:weighted_score,...},...}
    kkv = tuples_to_kkv(weighted)
    # sum weighted scores:     {j:weighted_average_scores,...}
    summed = {j:sum(qtos.values()) for j,qtos in kkv.items()}
    
    return summed



def grade_reviews_from_accessor(accessor, assignmentID, skip_loss, courseID = None):

    ### BASIC ALGORITHM:
    ###   1. grade each rubric question separately.
    ###   2. review grade is weighted average of question grades.
    if courseID == None:
        courseID = accessor.courseID

    # reviews: [(i,(j,q),score),...]    
    reviews = reviews_from_accessor(accessor,assignmentID,
                                    courseID=courseID)
    tas = accessor.get_tas_from_course(courseID)['taIDs']
    rubric_weights = accessor.get_rubric_weights(assignmentID)
    
    
    # peer_reviews: just the reviews of peers.
    peer_reviews = reviews_filter_peers(reviews,tas)
    # pull out and flatten the TA reviews: {(j,q):score,...}
    truths = truths_from_reviews(reviews,tas)

   
    return grade_reviews(peer_reviews,truths,rubric_weights,skip_loss)

# GRADE_PEERS
# Input:
#   reviews=[(i,(j,q),s),...] or {i:{j:s,...},...}
#   truths={(j,q):s,...}
#   weights={q:weight,...}
#   skip_loss = grade for skip.
# Output:
#   grades: {i:grade,...}
def grade_peers(reviews,truths,weights,skip_loss):
    reviews = ensure_tuples(reviews)
    
    questions = weights.keys()
    
    # grade each rubric question
    qreviews = {q:[(i,j,s) for (i,(j,qq),s) in reviews if qq == q] for q in questions}
    qtruths = {q:{j:s for (j,qq),s in truths.items() if qq == q} for q in questions}
    
    # qig_grades: {q:{i:g,...},...}
    qig_grades = {q:peer_grades(qreviews[q],qtruths[q],skip_loss) for q in questions}
    
    # indiv_grades: {i:{q:g,...},...}
    iqg_grades = kkv_invert(qig_grades)
    
    total_weight = sum(weights.values())
    # grades {i:weighted_average_grade,...}
    grades = {i:sum([g*weights[q] for q,g in qtog.items()]) for i,qtog in iqg_grades.items()}

    return grades

# GRADE_REVIEWS
# Input:
#   reviews=[(i,(j,q),s),...] or {i:{j:s,...},...}
#   truths={(j,q):s,...}
#   weights={q:weight,...}
#   skip_loss = grade for skip.
# Output:
#   grades: {i:{j:grade,...},...}
def grade_reviews(reviews,truths,weights,skip_loss):
    reviews = ensure_tuples(reviews)
    
    questions = weights.keys()
    
    # grade each rubric question
    qreviews = {q:[(i,j,s) for (i,(j,qq),s) in reviews if qq == q] for q in questions}
    qtruths = {q:{j:s for (j,qq),s in truths.items() if qq == q} for q in questions}
    
    # qijg: {q:{i:{j:g,...},...},...}
    qijg = {q:review_grades(qreviews[q],qtruths[q],skip_loss) for q in questions}


    
    # collapes k = ij
    qkg = {q:{(i,j):g for i,jtog in ijtog.items() 
                      for j,g in jtog.items()} 
             for q,ijtog in qijg.items()}

    # indiv_grades: {k:{q:g,...},...}
    kqg = kkv_invert(qkg)
    

    # grades {k:weighted_sum_grade,...}
    kg = {k:sum([g*weights[q] for q,g in qtog.items()]) for k,qtog in kqg.items()}



    pairs = kg.items()


    return tuples_to_kkv([(i,j,g) for ((i,j),g) in pairs])

    
    
    
    
#
# preprocesses reviews and truths, runs vancouver, and returns submission grades (no variances)
#
def run_vancouver(reviews,truths,t=10):
    tuples = ensure_tuples(reviews)
    
        
    # remove NonScore (these correspond for SKIP or NO_ANSWER)
    tuples = [(i,j,s) for (i,j,s) in tuples if isinstance(s,Number)]
    # warn about truths with NonScores
    notruths = [j for (j,s) in truths.items() if not isinstance(s,Number)]
    logger.info('No TA grade for submissions %s.',notruths)
    # remove NonScores from truths
    truths = {j:s for (j,s) in truths.items() if isinstance(s,Number)}
    
    # need to make sure each submission has two or more peers.
    #    (a) strategy: for submissions with 1 or more review, add TA reviews.
    #    (b) note: there better be TA reviews for submissions with 1 
    #            or more review.
    #    (c) equivalently: from all reviews, remove TA if TA is only review.
    jis = tuples_to_kkv([(j,i,s) for (i,j,s) in tuples])
    
    # implement (c), but doesn't check that removed review is TA review.
    jis_multiples = {j:itos for j,itos in jis.items() if len(itos) > 1}
    # convert back to [(i,j,s),...]
    tuples = [(i,j,s) for (j,i,s) in kkv_to_tuples(jis_multiples)]

    # we better have ground truth for all removed reviews.
    j_singles = set([j for j,itos in jis.items() if len(itos) <= 1])
    submissions_without_review = j_singles.difference(set(truths.keys()))
  
    if submissions_without_review:
        logger.error('insufficient peer reviews to grade submissions %s without TA reviews.',submissions_without_review)
    
    # need to make sure each peer has two or more reviews.
    #    (a) this really should not ever happen.  
    #    (b) strategy: merge all peers with a single submission into one peer.
    ijs = tuples_to_kkv(tuples)

    # remove peers with one or fewer reviews.
    ijs_multiples = {i:jtos for i,jtos in ijs.items() if len(jtos) > 1}

    # orphaned reviews from removed peers.
    orphaned_reviews = {j:s for i,jtos in ijs.items() if len(jtos) <= 1
                            for j,s in jtos.items()} 
    if orphaned_reviews:
        onereview_peers = [i for i,jtos in ijs.items() if len(jtos) <= 1]
        logger.warn('peers %s have only performed one review.',onereview_peers)
    
        ijs_multiples['metapeer'] = orphaned_reviews
    
    
    reviews = ijs_multiples

    # call vancouver
    (scores,qualities) = vancouver(reviews,{},t)
    
    grades = {j:s for j,(s,var) in scores.items()}

    return grades 


