from __future__ import division
from ..api import api
from ..algo.util import *
from ..jobs import match
from ..jobs import grading
from ..jobs import email
from ..jobs import canvas
from pprint import pprint
from copy import deepcopy
import time

import logging
logger = logging.getLogger()


job_name = 'appeals'
job_summary = 'Assign TAs to grade appeals'

default_params = {'tas':None}


def run(accessor,assignmentID,courseID=None,**params):

    if not courseID:
        courseID = accessor.courseID

    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID=courseID)
    d_params.update(a_params)
    params = d_params

    tas = params['tas']
    if not tas:
        tas = accessor.get_tas_from_course(courseID=courseID,markingLoad=1)

    logger.info("Executing appeals") 



    subs = accessor.get_appeal_submissions(assignmentID,courseID=courseID)

    # no appeals
    if not subs:
        logger.info("No appealed submissions")
        return True

    
    logger.info("Assigning appeals %s to TAs %s",str(subs),str(tas))
    r = match.insert_ta_matches_from_accessor(accessor,assignmentID, subs, tas = tas)

    if not r.ok:
        logger.warn("failed to insert matches")
        logger.warn("%s",r.text)
        return False
    
    if not email_tas_about_appeals(accessor,assignmentID,tas,courseID=courseID):
        logger.warn("failed to send emails to TA.  Notify TAs manually.")

    return True



def email_tas_about_appeals(accessor,assignmentID,tas,courseID=None):

    date_format = "%I:%M %p, %A, %B %d"

    subject = "Appeal reviews for '%(assignment_name)s' are assigned."

    message="""
Appeals for '%(assignment_name)s' are now closed.  You have %(missing_reviews)d required appeal reviews.  Please go to Mechanical TA to enter these reviews using the rubric and same criteria by which you entered your original reviews.  If you want to see why the submission grade was appealed you can access this information by searching the marking page for 'appeals'.
"""
    def date(utc):
        return time.strftime(date_format,time.localtime(int(utc)))

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    missing = grading.missing_truths_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)
    if not missing:
        logger.info("no outstanding TA reviews, no emails sent")
        return True


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

        if ta not in missing:
            continue

        params['missing_reviews'] = len(missing[ta])

        if ta in addresses:
            success = email.send(addresses[ta],subject % params, message % params)
    
        else:
            logger.warn("no email address found for TA %d, cannot send email.",ta)
 
    return success


    


def get_appeal_submissions(accessor,assignmentID,courseID=None):

    return accessor.get_appeal_submissions(assignmentID,courseID=courseID)


def set_appeal_grades(accessor,assignmentID,courseID=None):
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    subs = accessor.get_appeal_submissions(assignmentID,courseID=courseID)

    tas = accessor.get_tas(courseID=courseID)
    
    reviews = grading.reviews_from_accessor(accessor,assignmentID,courseID=courseID)

    missing = grading.missing_truths_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)
    if missing:
        logger.warn("TA grades are missing")
        logger.warn("%s",str(missing))
        return False

    # filter by TAs and subs.
    reviews = {(j,q):s for (i,(j,q),s) in ensure_tuples(reviews) if i in tas and j in subs}

    weights = accessor.get_rubric_weights(assignmentID)

    grades = grading.weighted_average_across_questions(reviews,weights)
    if not grades:
        logger.info("no appealed grades")
        return True

    logger.info("setting grades %s",str(grades))

    grade_data = grading.prepare_submission_grades(grades)

    r = accessor.set_submission_grades(assignmentID,grades=grade_data,mode=api.REPLACE_GRADE,courseID=courseID)

    if not r.ok:
        logger.warn("failed set grades")
        return False

    return True
    
    
    
    

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


        
        
