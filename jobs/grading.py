from ..api import api
from ..algo import review_grades 

import requests
from copy import deepcopy

from ..algo.vancouver import *
from ..algo.util import *
from numbers import Number
from ..algo.peer_assignment import cover_check

import operator


import logging
#logger = logging.getLogger('mtalib.jobs.grading')
logger = logging.getLogger()


job_name = 'grading'
job_summary = 'Grade submissions and peer reviews'

default_params = {'submission_bonus': 5.0,
                  'peerreview_average': 85.0,
                  'scoring_rule':'linear'}

def mixed_loss(truth,score):
    return .5 * review_grades.quadratic_loss(truth,score) + .5 * review_grades.linear_loss(truth,score)


loss_function = {'linear':review_grades.linear_loss,
                 'quadratic':review_grades.quadratic_loss,
                 'mixed':mixed_loss}

default_loss = review_grades.linear_loss


def run(accessor,assignmentID,courseID=None,**params):

    if not courseID:
        courseID = accessor.get_courseID(assignmentID)

    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID=courseID)
    d_params.update(a_params)
    params = d_params

    submission_bonus = params['submission_bonus']
    peerreview_average=params['peerreview_average']
    loss = loss_function[params['scoring_rule']]

    missing = missing_truths_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)

    if missing:
        logger.warn("Some TA grades are missing for assignment %d.")
        ta_records = key_on(accessor.get_users(courseID,users=missing.keys()),'userID')
        for ta in missing.keys():
            logger.warn("Grader %s has %d missing reviews.",ta_records[ta]['firstName'],len(missing[ta]))
 
        return False
    

    return run_submission(accessor,assignmentID,courseID=courseID,bonus=submission_bonus) \
        and run_peerreview(accessor,assignmentID,courseID=courseID,average=peerreview_average,loss=loss)

def run_submission(accessor,assignmentID,courseID=None,bonus=0.0):
    if courseID == None:
        courseID = accessor.get_courseID(assignmentID)


    logger.info("Executing submission grading, bonus=%f.",bonus)    

    r = execute_submission_grading(accessor,assignmentID,bonus=bonus,mode=api.REPLACE_GRADE,courseID=courseID)


    return r.status_code == requests.codes.ok


def run_peerreview(accessor,assignmentID,courseID=None,average=None,loss=default_loss):
    if courseID == None:
        courseID = accessor.get_courseID(assignmentID)


    if average:
        logger.info("Executing peerreview grading, average=%d.",average)    
    else:
        logger.info("Executing peerreview grading.",average)    

    r = execute_peerreview_grading(accessor,assignmentID,average=average,mode=api.REPLACE_GRADE,loss=loss,courseID=courseID)

    return r.status_code == requests.codes.ok





def mechta_reviews_from_accessor(accessor,assignmentID,courseID=None,rewrites={None:review_grades.NO_ANSWER,'Skip':review_grades.SKIP}):

    return accessor.get_peerreview_scores(assignmentID, courseID, rewrites)

####
# convert peerreviews from MechTA to [(i,(j,q),s),...] format:
#    - i: peerID
#    - j: submissionID
#    - q: questionID (in the rubric)
#    - s: score.
#
def mechta_reviews_to_reviews(mechta_reviews,peer_key='reviewerID'):
    tuples = [(review[peer_key],(j,q),response['score']) 
                 for j,reviews in mechta_reviews.items()
                 for review in reviews
                 for q,response in review['answers'].items() if 'score' in response]
    return tuples

# gives [(i,j,match_id),...]
def mechta_reviews_to_matchids(mechta_reviews,id_key='matchID'):
    tuples = [(review['reviewerID'],j,review[id_key]) 
                 for j,reviews in mechta_reviews.items()
                 for review in reviews]
    return tuples




 


def reviews_from_accessor(accessor,assignmentID,courseID=None,rewrites={None:review_grades.NO_ANSWER,'Skip':review_grades.SKIP},peer_key='reviewerID'):
    
    return mechta_reviews_to_reviews(mechta_reviews_from_accessor(accessor,assignmentID,courseID,rewrites),peer_key)

def tas_from_accessor(accessor,courseID=None):
    if not courseID:
        courseID = accessor.courseID

    return accessor.get_tas_from_course(courseID)

def truths_from_accessor(accessor,assignmentID,courseID=None,rewrites={None:review_grades.NO_ANSWER,'Skip':review_grades.SKIP},peer_key='reviewerID'):
    reviews = reviews_from_accessor(accessor,assignmentID,courseID=courseID,rewrites=rewrites)
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    tas = tas_from_accessor(accessor,courseID=courseID)

    return truths_from_reviews(reviews,tas)

def missing_truths_from_accessor(accessor,assignmentID,courseID=None,tas=None):
    reviews = reviews_from_accessor(accessor,assignmentID,courseID)

    if not tas:
        tas = tas_from_accessor(accessor,courseID)
    
    return missing_truths(reviews,tas)

# returns the first element if collection, or identity otherwise.
def first(j):
    try:
        return j[0]
    except TypeError:
        return j

# returns submissions with missing TA reviews.
def missing_truths(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    ta_tuples = reviews_filter_tas(tuples,tas)
   
    missing_pairs = [(i,j) for (i,j,s) in ta_tuples if not isinstance(s,Number)]

    if not missing_pairs:
        return {}
    
    missing_pairs = list(set([(i,first(j)) for (i,j) in missing_pairs]))
    
    return pairs_to_kvs(missing_pairs)



def truths_to_cover(truths):
    return list(set([first(j) for j in truths.keys()]))
    
def reviews_to_matches(reviews):
    reviews = ensure_tuples(reviews)

    # remove score and convert j or (j,q) to just j.
    matches = list(set([(i,first(j)) for (i,j,_) in reviews]))

    return matches

def reviews_to_matches(reviews):
    reviews = ensure_tuples(reviews)

    # remove score and convert j or (j,q) to just j.
    matches = list(set([(i,first(j)) for (i,j,_) in reviews]))

    return matches

def reviews_to_submissions(reviews):

    reviews = ensure_tuples(reviews)

    # remove i,score and convert j or (j,q) to just j.
    submissions = list(set([first(j) for (i,j,_) in reviews]))
    
    return submissions





    


#####
# convert peer review tuples from both TAs and peers 
#    tuples: [(i,jq,s),..] 
#    tas: [i,...]
# to the vancouver format:
#    reviews: {i:{jq:s,...},...}
#    truths: {js:s,...}
#
#    note: if all TA scores for a submission are review_grades.NO_ANSWER 
#          then review_grades.NO_ANSWER is the score returned.
def truths_from_reviews(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    ta_tuples = reviews_filter_tas(tuples,tas)
    

    missing = missing_truths(ta_tuples,tas)
    if missing:
        logger.warn("missing TA reviews by TAs %s for submissions %s",missing.keys(),list(set([j for js in missing.values() for j in js])))
    

    def avg_scores(scores):
        numeric_scores = [s for s in scores if isinstance(s,Number)]
        return avg(numeric_scores) if numeric_scores else review_grades.NO_ANSWER

    ta_kkv = tuples_to_kkv([(j,i,s) for (i,j,s) in ta_tuples])
    truths = {j:avg_scores(itos.values()) for j,itos in ta_kkv.items()}
    
    return truths

def reviews_filter_tas(reviews,tas):
    tuples = ensure_tuples(reviews)
    
    filtered = [(i,jq,s) for (i,jq,s) in tuples if int(i) in tas]
    return filtered

def reviews_filter_peers(reviews,tas):
    tuples = ensure_tuples(reviews)

    filtered = [(i,jq,s) for (i,jq,s) in tuples if int(i) not in tas]
    return filtered


def grading_errors(accessor,assignmentID,courseID=None,t=10):
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    reviews = reviews_from_accessor(accessor,assignmentID, courseID)
    tas = tas_from_accessor(accessor,courseID)
    weights = accessor.get_rubric_weights(assignmentID)
    # pull out and flatten the TA reviews.
    truths = truths_from_reviews(reviews,tas)

    (reviews,truths) = prepare_for_vancouver(reviews,truths)
    # call vancouver
    (scores,qualities) = vancouver(reviews,truths,t)

    (graded, ungraded) = vancouver_errors(reviews,truths,scores,qualities,tas)

    graded = weighted_average_across_questions(graded,weights)
    ungraded = weighted_average_across_questions(ungraded,weights)

    def sort_on_value(d):
        return sorted(d.items(),key=lambda (a,b):b,reverse=True)

    return (sort_on_value(graded),sort_on_value(ungraded))


    return (graded,ungraded)


#
# returns: {submission: grade, ...}
#

def grade_assignment(accessor, assignmentID, courseID = None,t=10):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    grades = grade_assignment_per_rubric(accessor,assignmentID,courseID,t)
    weights = accessor.get_rubric_weights(assignmentID)
    return weighted_average_across_questions(grades,weights)

def grade_assignment_per_rubric(accessor, assignmentID, courseID = None,t=10):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)
    
    reviews = reviews_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)
    tas = tas_from_accessor(accessor,courseID)

    
    # pull out and flatten the TA reviews.
    truths = truths_from_reviews(reviews,tas)
    
    # run vancouver
    grades = run_vancouver(reviews,truths,t)
    
    ###
    # reweight grades across rubric and sum.
    ###
    
    return grades


# WEIGHTED_AVERAGE_ACROSS_QUESTIONS
# Input:
#    grades: {(j,q):grade,...}
#    weights: {q:weight,...}
# Output:
#    summed: {j:weighted_grade,...}
def weighted_average_across_questions(grades,weights):

    def prod(lst):
        return reduce(operator.mul,lst,1)

    # if weight is tiny, then use score multiplicatively.
    multiplier1 = {(j,score) for ((j,q),score) in grades.items() if weights[q] <= .001}
    multiplier2 = ensure_kvs(multiplier1)
    multiplier = {j:prod(scores) for j,scores in multiplier2.items()}

    weighted = {(j,q,score*weights[q]) for ((j,q),score) in grades.items()}
    # convert to kkv:              {j:{q:weighted_score,...},...}
    kkv = tuples_to_kkv(weighted)
    # sum weighted scores:     {j:weighted_average_scores,...}
 
    summed = {j:round(sum(qtos.values()),2) for j,qtos in kkv.items()}
    
    
    multiplied = {j:s*multiplier[j] for (j,s) in summed.items()} if multiplier else summed

    return multiplied


def grade_reviews_from_accessor(accessor, assignmentID, skip_loss, loss=default_loss, average=None, courseID = None):

    ### BASIC ALGORITHM:
    ###   1. grade each rubric question separately.
    ###   2. review grade is weighted average of question grades.
    if courseID == None:
        courseID = accessor.courseID

    # reviews: [(i,(j,q),score),...]    
    reviews = reviews_from_accessor(accessor,assignmentID,
                                    courseID=courseID)
    tas = tas_from_accessor(accessor,courseID)
    rubric_weights = accessor.get_rubric_weights(assignmentID)
    
    
    # peer_reviews: just the reviews of peers.
    peer_reviews = reviews_filter_peers(reviews,tas)
    # pull out and flatten the TA reviews: {(j,q):score,...}
    truths = truths_from_reviews(reviews,tas)

   
    return grade_reviews(peer_reviews,truths,rubric_weights,skip_loss,loss,average)

# GRADE_PEERS
# Input:
#   reviews=[(i,(j,q),s),...] or {i:{j:s,...},...}
#   truths={(j,q):s,...}
#   weights={q:weight,...}
#   skip_loss = grade for skip.
# Output:
#   grades: {i:grade,...}
def grade_peers(reviews,truths,weights,skip_loss,loss=mixed_loss):
    reviews = ensure_tuples(reviews)
    
    questions = weights.keys()
    
    # grade each rubric question
    qreviews = {q:[(i,j,s) for (i,(j,qq),s) in reviews if qq == q] for q in questions}
    qtruths = {q:{j:s for (j,qq),s in truths.items() if qq == q} for q in questions}
    
    # qig_grades: {q:{i:g,...},...}
    qig_grades = {q:review_grades.peer_grades(qreviews[q],qtruths[q],skip_loss,loss) for q in questions}
    
    # indiv_grades: {i:{q:g,...},...}
    iqg_grades = kkv_invert(qig_grades)
    
    total_weight = sum(weights.values())
    # grades {i:weighted_average_grade,...}
    grades = {i:round(sum([g*weights[q] for q,g in qtog.items()]),1) for i,qtog in iqg_grades.items()}

    return grades

    


# GRADE_REVIEWS
# Input:
#   reviews=[(i,(j,q),s),...] or {i:{j:s,...},...}
#   truths={(j,q):s,...}
#   weights={q:weight,...}
#   skip_loss = grade for skip.
# Output:
#   grades: {i:{j:grade,...},...}
def grade_reviews(reviews,truths,weights,skip_loss,loss=mixed_loss,average=None,question_average=None):

    if question_average:
        logger.info("Grading Reviews with per-rubric question average boosted to %f",question_average)

    reviews = ensure_tuples(reviews)
    
    questions = weights.keys()

    # remove ungraded submissions from truths.
    ungraded = list(set([j for (j,q),g in truths.items() if not isinstance(g,Number)]))
    if ungraded:
        logger.warn("ungraded submissions: %s",ungraded)
    truths = {j:g for j,g in truths.items() if isinstance(g,Number)}

    # grade each rubric question
    qreviews = {q:[(i,j,s) for (i,(j,qq),s) in reviews if qq == q] for q in questions}
    qtruths = {q:{j:s for (j,qq),s in truths.items() if qq == q} for q in questions}
    
    # qijg: {q:{i:{j:g,...},...},...}
    qijg = {q:review_grades.review_grades(qreviews[q],qtruths[q],skip_loss,loss,question_average) for q in questions}


    
    # collapes k = ij
    qkg = {q:{(i,j):g for i,jtog in ijtog.items() 
                      for j,g in jtog.items()} 
             for q,ijtog in qijg.items()}

    # indiv_grades: {k:{q:g,...},...}
    kqg = kkv_invert(qkg)
    

    # grades {k:weighted_sum_grade,...}
    kg = {k:sum([g*weights[q] for q,g in qtog.items()]) for k,qtog in kqg.items()}



    pairs = kg.items()

    grades = [(i,j,g) for ((i,j),g) in pairs]

    # raise grades up so that average is 'average'
    if average:
        total = sum(weights.values())

        jtoigs = ensure_kvs([(j,(i,g)) for (i,j,g) in grades])
        
        avgs = {j:avg([g for (_,g) in igs]) for j,igs in jtoigs.items()}

        def raise_avg(g,avg):
            return (total-(total-g)/(total-avg)*(total-average)) if avg < average else g

        grades = [(i,j,raise_avg(g,avgs[j])) for (i,j,g) in grades]

    return tuples_to_kkv(grades)

    
    
    
    
#
# preprocesses reviews and truths, runs vancouver, and returns submission grades (no variances)
#
def prepare_for_vancouver(reviews,truths):
    tuples = ensure_tuples(reviews)
    
        
    # remove NonScore (these correspond for SKIP or NO_ANSWER)
    tuples = [(i,j,s) for (i,j,s) in tuples if isinstance(s,Number)]
    # warn about truths with NonScores
    notruths = [j for (j,s) in truths.items() if not isinstance(s,Number)]
    if notruths:
        logger.info('No TA grade for submissions %s.',notruths)
    # remove NonScores from truths
    truths = {j:s for (j,s) in truths.items() if isinstance(s,Number)}



    # input: tuples; output: tuples

    # need to make sure each peer has two or more reviews.
    #    (a) this really should not ever happen.  
    #    (b) strategy: merge all peers with a single submission into one peer.
    #    (c) if it's only one peer, discard review.
    ijs = tuples_to_kkv(tuples)

    # remove peers with one or fewer reviews.
    ijs_multiples = {i:jtos for i,jtos in ijs.items() if len(jtos) > 1}

    # orphaned reviews from removed peers.
    orphaned_reviews = {j:s for i,jtos in ijs.items() if len(jtos) <= 1
                            for j,s in jtos.items()}

    # add orphaned reviews as one peer; or discard if only one.
    if orphaned_reviews:
        onereview_peers = [i for i,jtos in ijs.items() if len(jtos) <= 1]
        logger.warn('peers %s have only performed one review.',onereview_peers)
    
        if len(orphaned_reviews) > 1:
            ijs_multiples['metapeer'] = orphaned_reviews

    tuples = kkv_to_tuples(ijs_multiples)


    # input: tuples; output: tuples
    
    # need to make sure each submission has two or more peers.
    #    (a) strategy: for submissions with 1 or more review, add TA reviews.
    #    (b) note: there better be TA reviews for submissions with 1 
    #            or fewer review.
    #    (c) equivalently: from all reviews, remove TA if TA is only review.
    jis = tuples_to_kkv([(j,i,s) for (i,j,s) in tuples])
    
    # implement (c), but doesn't check that removed review is TA review.
    jis_multiples = {j:itos for j,itos in jis.items() if len(itos) > 1}
    # convert back to [(i,j,s),...]
    tuples = [(i,j,s) for (j,i,s) in kkv_to_tuples(jis_multiples)]

    # we better have ground truth for all removed reviews.
    j_singles = set([j for j,itos in jis.items() if len(itos) <= 1])
    if j_singles:
        logger.warn('only single review for submissions %s',j_singles)
    submissions_without_review = j_singles.difference(set(truths.keys()))
  
    if submissions_without_review:
        logger.error('insufficient peer reviews to grade submissions %s without TA reviews.',submissions_without_review)
    


    # convert to kvv for output.
    reviews = tuples_to_kkv(tuples)

    return (reviews,truths)


def run_vancouver(reviews,truths,t=10):
    (reviews,truths) = prepare_for_vancouver(reviews,truths)
    # call vancouver
    (scores,qualities) = vancouver(reviews,truths,t)
    
    grades = {j:s for j,(s,var) in scores.items()}

    # add back in singles these did not get a grade in vancouver
    # because we removed them.
    #####grades.update({j:truths[j] for j in j_singles})
    grades.update(truths)

    return grades 




def execute_submission_grading(accessor,assignmentID,courseID=None,bonus=0.0,mode=api.REPLACE_GRADE):
    
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    subgrades = grade_assignment(accessor,assignmentID=assignmentID,courseID=courseID)

    logger.info("setting %d submission grades",len(subgrades))


    r = accessor.set_submission_grades(assignmentID=assignmentID,
                                       courseID=courseID,
                                       grades=[{'submissionID':int(j),
                                                'grade':round(g + bonus,1)} 
                                               for j,g in subgrades.items()],
                                       mode=mode)
    return r

# [(j,g),...] => [{'submissionID':j,'grade':g},...]
#    or
# {j:g,...} => [{'submissionID':j,'grade':g},...]

def prepare_submission_grades(grades):
    if isinstance(grades,dict):
        grades = grades.items()

    return [{'submissionID':int(j),
             'grade':round(g,1)} for j,g in grades]

# returns list of peers with no review grade.
def ungraded_peers(accessor,assignmentID):

    # revgrades: {i:{j:g,...},...}
    # note: doesn't contain peers with no grade.
    revgrades = grade_reviews_from_accessor(accessor, assignmentID=assignmentID, skip_loss=0.5,loss=mixed_loss)

    all_peers = ensure_kkv(reviews_from_accessor(accessor,assignmentID)).keys()
    graded_peers = revgrades.keys()
    ungraded = list(set(all_peers) - set(graded_peers))
    
    counts = pairs_to_kvs([(len(jtog),i) for i,jtog in revgrades.items()])
    counts[0] = ungraded
    
    return counts



def execute_peerreview_grading(accessor,assignmentID,courseID=None,average=None,mode=api.REPLACE_GRADE,loss=default_loss):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    revgrades = grade_reviews_from_accessor(accessor, assignmentID=assignmentID,courseID=courseID, skip_loss=0.5,loss=loss,average=average)


    mta_reviews = mechta_reviews_from_accessor(accessor,courseID=courseID,assignmentID=assignmentID)
    matchids = mechta_reviews_to_matchids(mta_reviews)


    ij2m = kkv_to_kv(matchids)
    ij2g = kkv_to_kv(revgrades)

    # mgs: [(matchID,grade),...]
    mgs = [(ij2m[ij],ij2g[ij]) for ij in ij2g.keys()]


    mechta_match_grades = [{'matchID':int(m),'grade':round(g,1)} for m,g in mgs]

    logger.info("setting %d peerreview grades",len(mechta_match_grades))

    r = accessor.set_review_grades(assignmentID,mechta_match_grades,mode=mode,courseID=courseID)
    return r


def execute(accessor,assignmentID,courseID=None):
    execute_peerreview_grading(accessor,assignmentID,courseID=courseID)
    execute_submission_grading(accessor,assignmentID,courseID=courseID)


def get_review_grades(accessor,assignmentID,courseID=None):
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    
    revgrades = accessor.get_peerreview_grades(assignmentID,courseID=courseID)
    
    # grade is the maximum review score.
    revgrades = tuples_to_kkv([(d['reviewerID'],d['submissionID'],d['grade']) for d in revgrades])
    revgrades = [(i,max(jtog.values())) for i,jtog in revgrades.items()]
    
    return revgrades


def get_submission_grades(accessor,assignmentID,courseID=None,bonus=0.0):
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    

    subgrades = accessor.get_submission_grades(assignmentID,courseID=courseID)
    subgrades = [(d['studentID'],d['grade']) for d in subgrades]

    submitters = [i for (i,_) in subgrades]
    students = accessor.get_students(courseID=courseID)
    non_submitters = list(set(students) - set(submitters))
    
    subgrades += [(i,bonus) for i in non_submitters]

    return subgrades
