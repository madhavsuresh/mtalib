from __future__ import division
import random
from ..api.api import *
from ..algo.util import *
from . import cover
from . import match
from . import canvas
from . import email

from mtalib.jobs import grading
from numbers import Number
from copy import deepcopy




import logging
logger = logging.getLogger()


job_name = 'check_ta_reviews'
job_summary = 'Check that TA reviews are in and system is ready for grading algorithms to be run'


date_format = "%I:%M %p, %A, %B %d"

subject = "TA reviews for '%(assignment_name)s' are past due!"

message="""
You have %(missing_reviews)d required TA reviews for assignment '%(assignment_name)s' that are past due.  Please go to Mechanical TA to enter these reviews immediately.  
"""


default_params = {}

def run(accessor,assignmentID,courseID=None,**params):

    if not courseID:
        courseID = accessor.get_courseID(assignmentID)

    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID)
    d_params.update(a_params)
    params = d_params


    # welcome message
    logger.info("Executing %s.",job_name) 


    def date(utc):
        return time.strftime(date_format,time.localtime(int(utc)))


    missing = grading.missing_truths_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)
    if not missing:
        logger.info("no outstanding TA reviews, no emails sent")
        return True

    tas = missing.keys()

    # get assignment name
    assn = accessor.get_assignment(assignmentIDs = [assignmentID],courseID=courseID)

    if len(assn) == 1:
        assn = assn[0]
        params = {
            'assignment_name': assn['name'],
            'mark_post_date': date(assn['markPostDate']),
            'review_stop_date': date(assn['reviewStopDate'])
            }
    else:
        logger.warn("unable to get assignment details for assignment %d",assignmentID)
        params = {
            'assignment_name': "Unknown Assignment",
            'mark_post_date': "Unknown Date",
            'review_stop_date': "Unknown Date"
            }

    addresses = canvas.get_emails(accessor,courseID=courseID)

    success = False

    for ta in tas:

        params['missing_reviews'] = len(missing[ta])

        if ta in addresses:
            success = email.send(addresses[ta],subject % params, message % params)    
        else:
            logger.warn("no email address found for TA %d, cannot send email.",ta)

    if not success:
        logger.warn("Failed to send some emails.  Contact TAs manually.")

    return False






anonymous_username = 'anonymous'
anonymous_usertype = 'anonymous'

anonymous_user_data = {
  'firstName': 'Anonymous',
  'lastName': 'Student',
  'studentID': '999999',
  'userType': anonymous_usertype,
  'username': anonymous_username}

def get_anonymous(accessor,courseID=None):
    if not courseID:
        courseID = accessor.courseID

    # find the anonymous users if one exists.
    users = accessor.get_all_users(courseID=courseID)

    anons = [u for u in users if u['username'] == anonymous_username]

    # add an anoymous users if there are none.
    if not anons:
        accessor.create_users(courseID=courseID,list_of_users=[anonymous_user_data])
        users = accessor.get_all_users(courseID=courseID)
        anons = [u for u in users if u['username'] == anonymous_username and u['userType'] == anonymous_usertype]

    if not anons:
        logger.error("unable to find (or create) anonymous user")
        return 0

    if len(anons) >= 2:
        logger.warn("more than two anonymous users")

    return anons[0]['userID']
    


def reviews_simple_average(accessor, assignmentID, subs,courseID=None):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    revs = grading.reviews_from_accessor(accessor,assignmentID,courseID=courseID)
    revs = [((int(j),q),s) for (i,(j,q),s) in revs if int(j) in subs and isinstance(s,Number)]
    kvs = pairs_to_kvs(revs)

    kv = [(jq,avg(scores)) for jq,scores in kvs.items()]
    
    tuples = [(j,q,s) for ((j,q),s) in kv]
    
    return tuples_to_kkv(tuples)

    
# the strategy for insufficient reviews, which there are a lot:
#    - reviews with scores all in 8,9,10: assign anonymous reviews of all 10s.
#    - reviews with scores <= 7: assign to TAs to review.

def patch_insufficiently_reviewed(accessor, assignmentID, courseID=None, required=2,limit=0.5, tas=None, doit=True):

    success = False

    if not courseID:
        courseID = accessor.get_courseID(assignmentID)


    subs = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=courseID,required=required)]

    if not subs:
        logger.info("No insufficiently reviewed submissions")
        return (True,[],[])

    logger.info("Patching %d insufficiently reviews submissions", len(subs))
    
    # 'missing' must be reviewed.
    missing = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=courseID,required=1)]
    # 'subs' are remaining reviews.
    subs = list(set(subs) - set(missing))

    if missing:
        logger.info("Submissions with no reviews: %s",str(missing))
        if doit:
            match.insert_ta_matches_from_accessor(accessor,assignmentID,missing,tas,couseID=courseID)
    
    
    if subs:
        logger.info("Generating anonymous review for %d submissions with one review: %s",len(subs),str(subs))

        anon = get_anonymous(accessor,courseID=courseID)

        scores = reviews_simple_average(accessor,assignmentID,subs,courseID=courseID)
        add_anonymous_reviews(accessor,assignmentID,subs,anon=anon,scores=scores,doit=doit,courseID=courseID)

    
 
    if doit:
        final_remaining = [int(j) for j in cover.insufficiently_reviewed_from_accessor(accessor,assignmentID,courseID=courseID,required=2)]
        if final_remaining:
            # see if we have anything left uncovered.
            
            logger.warn("Insufficiently reviewed submissions remain: %s",str(final_remaining))         
#            revs = grading.reviews_from_accessor(accessor,assignmentID)
#            revs = [(int(j),(i,q),s) for (i,(j,q),s) in revs if int(j) in final_remaining and isinstance(s,Number)]
#            kkv = tuples_to_kkv(revs)
#            pprint(kkv)
            success = False
        else:
            success=True
            logger.info("No remaining insufficiently reviewed submissions.")

    return (success,missing,subs) 


# returns the integer corresponding to a random score based on avg_score.
# currently this is something like U[avg_score,.5 + avg_score/2]
def random_anonymous_score(avg_score):
    score = random.uniform(avg_score,.55 + avg_score/2)
    return 10 - int(score*10)  # map 1.0 to 0, 0.9 to 

# scores: {j:{q:score,...},...}
def add_anonymous_reviews(accessor,assignmentID,subs,anon,scores={},doit=True,courseID=None):
    
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)



    def score(j,q):
        return scores[j][q] if j in scores and q in scores[j] else 1.0
           
    logger.info("Adding matches for anonymous reviews")
    if doit:
        match.insert_matches_from_accessor(accessor,assignmentID, user = anon, subs = subs,courseID=courseID)

        # get MATCHIDS
        mta_reviews = grading.mechta_reviews_from_accessor(accessor,assignmentID)
        matches = grading.mechta_reviews_to_matchids(mta_reviews)
        matchids = {int(mid):int(j) for (i,j,mid) in matches if int(i) == anon}
        logger.info("%d MATCHIDS: %s", len(matchids),str(matchids.keys()))
    else:
        # fake matchids
        matchids = {j:j for j in subs}
        logger.info("%d FAKED MATCHIDS: %s", len(matchids),str(matchids.keys()))

    
    
    rubric = accessor.get_rubric(courseID=courseID,assignmentID=assignmentID)
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

