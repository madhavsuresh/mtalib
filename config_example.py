# copy to config.py

from api.api import server_accessor
from jobs import events
from jobs import match
from jobs import patch_reviews
from jobs import grading
from jobs import canvas
from jobs import appeals
from jobs import update_enrollments
from jobs import upload_grades
from jobs import upload_appeal_grades
from jobs import check_ta_reviews
from pprint import pprint

import logging
import sys
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

courses = [2,3,4]

canvas.set_access_token("ENTER TOKEN HERE")

api_server_live = server_accessor('https://mech-ta.eecs.northwestern.edu/mta/api/',username='qGrHbWYiAzWwRN0uG5dFimLgU5dqFcf',password='7x1kRZATsQrMq1f7ukKZtkM0bonwbSB',confirm_post=True,check_courseID=True)

api_server_test = server_accessor('http://enron.cs.northwestern.edu/~madhav/treftun/mta/api/', username='root', password='password')

api_server=api_server_live

prompt = True

## update enrollments
events.add_datehook(job = update_enrollments.job_name, 
                    summary = update_enrollments.job_summary, 
                    event=events.submission_stop, 
                    execute = update_enrollments.run, 
                    grace=False,
                    delay=-120
                   )



## PEER MATCH
events.add_datehook(job = match.job_name, 
                    summary = match.job_summary, 
                    event=events.submission_stop, 
                    execute = match.run, 
                    grace=True,
                    delay=10,
                    params={'ta_load':10,'peer_load':3,'tas':None}
                   )

# PATCH_REVIEWS
events.add_datehook(job = patch_reviews.job_name, 
                    summary = patch_reviews.job_summary, 
                    event=events.review_stop, 
                    execute = patch_reviews.run, 
                    grace = True,
                    delay=100,
                    params={'required_reviews':2}
                   )

# CHECK_TA_REVIEWS
events.add_datehook(job = check_ta_reviews.job_name, 
                    summary = check_ta_reviews.job_summary, 
                    event=events.review_stop, 
                    execute = check_ta_reviews.run, 
                    grace = False,
                    delay=60 * 24 # one day.
                   )


# POST GRADES
events.add_datehook(job = grading.job_name, 
                    summary = grading.job_summary, 
                    event = events.mark_post, 
                    execute = grading.run, 
                    delay=-60 * 3,
                    params = {'submission_bonus':5.0,
                              'peerreview_average':85,
                              'scoring_rule':'linear'}
                   )

# upload grades to canvas
events.add_datehook(job = upload_grades.job_name, 
                    summary = upload_grades.job_summary, 
                    event = events.mark_post, 
                    execute = upload_grades.run, 
                    delay=60 * 24 * 1,
                    params = {'submission_bonus':5.0,
                              'submission_name':'Problem',
                              'review_name':'Peer Review'}
                   )

## PROCESS APPEALS
events.add_datehook(job = appeals.job_name, 
                    summary = appeals.job_summary, 
                    event=events.appeal_stop, 
                    execute = appeals.run, 
                    grace=True,
                    delay=60, # one hour
                    params={}
                   )

# upload grades to canvas
events.add_datehook(job = upload_appeal_grades.job_name, 
                    summary = upload_appeal_grades.job_summary, 
                    event = events.appeal_stop, 
                    execute = upload_appeal_grades.run, 
                    delay=60 * 24 * 7,
                    params = {'submission_bonus':5.0,
                              'submission_name':'Problem',
                              'review_name':'Peer Review'}
                   )


# events.add_datehook(job = match.job_name, 
#                     summary = match.job_summary, 
#                     event=events.submission_stop, 
#                     execute = match.run, 
#                     grace=True,
#                     delay=10,
#                     params={'ta_matching':ta_matching,'k':3,'cover_size':10,
#                             'dropped_students':dropped_students}
#                    )



# events.add_datehook(job=update_enrollments.job_name, 
#                     summary=update_enrollments.job_summary, 
#                     event=events.submission_stop,
#                     execute = update_enrollments.run, 
#                     delay=-1 * 12 * 60
#                    )

