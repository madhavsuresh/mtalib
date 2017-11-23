from __future__ import division
from time import time
from pprint import pprint
import StringIO
from ..api.api import server_accessor
import logging

logger = logging.getLogger()

# def job_assign_peer_reviews(accessor,hw):
    
#     logger.info("peermatch executed for assignment %d",hw)
    
#     return 1

# def job_post_grades(accessor,hw):
    
#     logger.info("grades posted for assignment %d",hw)

#     return 1

datehooks = []

datahook_keys = ['job','summary','event','delay','grace','execute','params']

def add_datehook(job,summary,event,execute,params={},grace=False,delay=0):
    datehooks.append(locals())

calibration_start = 'calibrationStartDate'
mark_post = 'markPostDate'
review_start = 'reviewStartDate'
calibration_stop = 'calibrationStopDate'
review_stop = 'reviewStopDate'
submission_start = 'submissionStartDate'
appeal_stop = 'appealStopDate'
submission_stop = 'submissionStopDate'

def run_noop(accessor,assignmentID,**params):
    logger.info("Job not executed.  Run manually.")
    return True

# datehooks = [{'job':'peermatch',
#               'summary':'Executed Peer Match for Assignment {assignmentID}',
#               'event':'submissionStopDate',
#               'delay': -20, # hours * minutes
#               'grace': 1, # offset deadline by graceperiod
#               'execute':job_assign_peer_reviews, # (accessor,hw) -> success
#               'params':{}},
#              {'job':'postgrades',
#               'summary':'Executed Post Grades for Assignment {assignmentID}',
#               'event':'markPostDate',
#               'delay': -30,    # minutes
#               'grace': 0, 
#               'execute':job_post_grades,
#               'params':{}}
#             ]

delay_multiplier_to_seconds = 60

def log_event(accessor,courseID=None,**eventlog):
    if not courseID:
        courseID = accessor.courseID


    logger.info("EVENT CREATED")
#    logger.info(eventlog)
    accessor.event_create(courseID=courseID,**eventlog)

def capture_log(f,**params):
    
    # ADD HANDLER
    stream = StringIO.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # CALL FUNCTION
    out = f(**params)
    
    # REMOVE HANDLER
    logger.removeHandler(handler)
    stream.flush()
    
    # RETURN FUNCTION OUTPUT AND LOG
    return (out,stream.getvalue())


def run(accessor,courseID=None,prompt=False):

    if not courseID:
        courseID = accessor.courseID

    print "Processing Events"
    
    course = accessor.get_course(courseID=courseID)
    grace = int(course['gracePeriod'])

    assignments = [a for a in accessor.get_assignment(courseID=courseID) if 'visibleToStudents' in a and int(a['visibleToStudents'])]
    

    events = accessor.event_get(courseID=courseID)
    
    now = int(time())
    
    # find dates that have passed and have not been processed.
    for datehook in datehooks:
        event = datehook['event']
        delay = datehook['delay'] + datehook['grace'] * grace 
        job = datehook['job']

        

        #
        #
        #
        if assignments and event not in assignments[0]:
            logger.warn("No event matches hook \'" + event + "\'")

        logger.info("")
        logger.info("BEGIN Processing job %s for event %s in course %d",datehook['job'],datehook['event'],courseID)
        


        #
        # CALCULATE PENDING ASSIGNMENTS
        #
        triggered = [a['assignmentID'] for a in assignments if event in a and int(a[event]) + delay * delay_multiplier_to_seconds < now]
        executed = [e['assignmentID'] for e in events if e['job'] == job]

        logger.info("Triggered: %s",str(triggered))
        logger.info("Previously executed: %s",str(executed))
              
        pending = list(set(triggered)-set(executed))
        
        if pending:
            logger.info("pending assignments for job %s course %d: %s",job,courseID,str(pending))
            if prompt:
                s = raw_input("Continue (y/n)?")
                if "n" in s:
                    print "skipping"
                    continue

        
        #
        # EXECUTE JOB FOR PENDING ASSIGMNENTS
        #
        execute = datehook['execute']
        params = datehook['params']

        for assignmentID in sorted(pending):
            
            # EXECUTE
            (success,details) = capture_log(lambda:execute(accessor,assignmentID,courseID=courseID,**params))
            
            # ADD EVENT TO LOG
            eventlog = {'job':job,
                        'summary':datehook['summary'].format(assignmentID=assignmentID),
                        'details':"<PRE>\n" + details + "</PRE>\n",
                        'success':success,
                        'assignmentID':assignmentID} 
           
            log_event(accessor,courseID=courseID,**eventlog)
    

        logger.info("END Processing job %s for event %s in course %d.",datehook['job'],datehook['event'],courseID)
        logger.info("")
