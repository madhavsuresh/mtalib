from __future__ import division
from ..api.api import *
from ..algo.util import *
from . import cover
import logging

logger = logging.getLogger()


anonymous_username = ' anonymous'
anonymous_user_data = {
  'firstName': 'Anonymous',
  'lastName': 'Student',
  'studentID': '999999',
  'userType': 'student',
  'username': anonymous_username},

def get_anonymous(accessor):

    # find the anonymous users if one exists.
    users = accessor.get_all_users()
    anons = [u for u in users if u['username'] == anonymous_username]

    # add an anoymous users if there are none.
    if not anons:
        accessor.create_users(list_of_users=[anonymous_user_data])
        users = accessor.get_all_users()
        anons = [u for u in users if u['username'] == anonymous_username]

    if not anons:
        logger.error("unable to find (or create) anonymous user")
        return 0

    if len(anons) >= 2:
        logger.warn("more than two anonymous users")

    return anons[0]['userID']
    


def reviews_simple_average(accessor, assignmentID, subs):
    revs = grading.reviews_from_accessor(accessor,assignmentID)
    revs = [((int(j),q),s) for (i,(j,q),s) in revs if int(j) in subs and isinstance(s,Number)]
    kvs = pairs_to_kvs(revs)

    kv = [(jq,avg(scores)) for jq,scores in kvs.items()]
    
    tuples = [(j,q,s) for ((j,q),s) in kv]
    
    return tuples_to_kkv(tuples)

    
# the strategy for insufficient reviews, which there are a lot:
#    - reviews with scores all in 8,9,10: assign anonymous reviews of all 10s.
#    - reviews with scores <= 7: assign to TAs to review.

def patch_insufficiently_reviewed(accessor, assignmentID, required=2,limit=0.5, tas=None, doit=True):
    subs = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=1,required=required)]

    if not subs:
        logger.info("No insufficiently reviewed submissions")
        return ([],[])

    logger.info("Patching %d insufficiently reviews submissions", len(subs))
    
    # 'missing' must be reviewed.
    missing = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=1,required=1)]
    # 'subs' are remaining reviews.
    subs = list(set(subs) - set(missing))

    if missing:
        logger.info("Submissions with no reviews: %s",str(missing))
        if doit:
            match.insert_ta_matches_from_accessor(accessor,assignmentID,missing,tas)
    
    
    if subs:
        logger.info("Generating anonymous review for %d submissions with one review: %s",len(subs),str(subs))

        anon = get_anonymous(accessor)

        scores = reviews_simple_average(accessor,assignmentID,subs)
        add_anonymous_reviews(accessor,assignmentID,subs,anon=anon,scores=scores,doit=doit)

    
 
    if doit:
        final_remaining = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=1,required=2)]
        if final_remaining:
            # see if we have anything left uncovered.
            
            logger.warn("Insufficiently reviewed submissions remain: %s",str(final_remaining))         
#            revs = grading.reviews_from_accessor(accessor,assignmentID)
#            revs = [(int(j),(i,q),s) for (i,(j,q),s) in revs if int(j) in final_remaining and isinstance(s,Number)]
#            kkv = tuples_to_kkv(revs)
#            pprint(kkv)
        else:
            logger.info("No remaining insufficiently reviewed submissions."

    return (missing,subs) 


# returns the integer corresponding to a random score based on avg_score.
# currently this is something like U[avg_score,.5 + avg_score/2]
def random_anonymous_score(avg_score):
    score = random.uniform(avg_score,.55 + avg_score/2)
    return 10 - int(score*10)  # map 1.0 to 0, 0.9 to 

# scores: {j:{q:score,...},...}
def add_anonymous_reviews(accessor,assignmentID,subs,anon,scores={},doit=True):

    def score(j,q):
        return scores[j][q] if j in scores and q in scores[j] else 1.0
           
    logger.info("Adding matches for anonymous reviews")
    if doit:
        match.insert_ta_matches_from_accessor(accessor,assignmentID, subs, tas = [anon])

        # get MATCHIDS
        mta_reviews = grading.mechta_reviews_from_accessor(accessor,assignmentID)
        matches = grading.mechta_reviews_to_matchids(mta_reviews)
        matchids = {int(mid):int(j) for (i,j,mid) in matches if int(i) == anon}
        logger.info("%d MATCHIDS: %s", str(len(matchids)),str(matchids.keys()))
    else:
        # fake matchids
        matchids = {j:j for j in subs}
        logger.info("%d FAKED MATCHIDS: %s", str(len(matchids)),str(matchids.keys()))

    
    
    rubric = accessor.get_rubric(assignmentID=assignmentID)
    questions = [q for q,r in rubric.items() if 'options' in r]
    answers = [{'match_id': matchid, 
                'question_id': q, 
                'answer_type': 'int',
                'answer_value': random_anonymous_score(score(j,q)),
                'score':score(j,q)
               } for q in questions for (matchid,j) in matchids.items()]

    logger.info("Adding anonymous reviews")
    if doit:
        accessor.create_peerreviews_bulk(answers)
    else:
        logger.info(str(answers))
    
    return matchids.keys()

