from __future__ import division
from time import time
from pprint import pprint
import StringIO
from ..api.api import accessor
import logging


# def job_assign_peer_reviews(accessor,hw):
    
#     logger.info("peermatch executed for assignment %d",hw)
    
#     return 1

# def job_post_grades(accessor,hw):
    
#     logger.info("grades posted for assignment %d",hw)

#     return 1


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

def log_event(accessor,**eventlog):
    logger.info("EVENT CREATED")
    logger.info(eventlog)
    accessor.event_create(**eventlog)

def capture_log(f):
    
    # ADD HANDLER
    stream = StringIO.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # CALL FUNCTION
    out = f()
    
    # REMOVE HANDLER
    logger.removeHandler(handler)
    stream.flush()
    
    # RETURN FUNCTION OUTPUT AND LOG
    return (out,stream.getvalue())


def run(accessor):
    course = accessor.get_course(courseID=accessor.courseID)
    grace = course['gracePeriod']

    assignments = accessor.get_assignment()
    events = accessor.event_get()
    
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
            print "WARNING: No event matches hook \'" + event + "\'"
        
        #
        # CALCULATE PENDING ASSIGNMENTS
        #
        triggered = [a['assignmentID'] for a in assignments if event in a and int(a[event]) + delay * delay_multiplier_to_seconds < now]
        executed = [e['assignmentID'] for e in events if e['job'] == job]
              
        pending = list(set(triggered)-set(executed))
        
        if pending:
            logger.info("pending homeworks for %s: %s",job,str(pending))
        
        #
        # EXECUTE JOB FOR PENDING ASSIGMNENTS
        #
        execute = datehook['execute']

        for assignmentID in sorted(pending):
            
            # EXECUTE
            (success,details) = capture_log(lambda:execute(accessor,assignmentID))
            
            # ADD EVENT TO LOG
            eventlog = {'job':job,
                        'summary':datehook['summary'].format(assignmentID=assignmentID),
                        'details':"<PRE>\n" + details + "</PRE>\n",
                        'success':success,
                        'assignmentID':assignmentID} 
           
            log_event(accessor,**eventlog)
    
