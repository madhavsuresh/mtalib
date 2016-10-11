from ..api import api
from datetime import datetime
from .. import config
import logging

logger = logging.getLogger('mtalib.events.event')

#retries will be handled manually
class EventAssignment:
    '''takes as input an assignment'''
    def __init__(self, assignment_id,api_server,course_id=None):
        self.api_server = api_server
        self.assignment_id = assignment_id
        if course_id:
            self.course_id = course_id
        else:
            self.course_id =int(api_server.get_courseID_from_assignmentID(
                  assignment_id)['courseID'])

        assignment = self.api_server.get_assignment_event(self.course_id,
                                                          self.assignment_id)
        assignment = assignment['assignmentList'][0]
        self.submissionStartDate = datetime.strptime(assignment['submissionStartDate'],
                                                      config.date_fmt)
        self.submissionStopDate = datetime.strptime(assignment['submissionStopDate'],
                                                     config.date_fmt)
        self.reviewStartDate = datetime.strptime(assignment['reviewStartDate'],
                                                 config.date_fmt)
        self.reviewStopDate = datetime.strptime(assignment['reviewStopDate'],
                                                 config.date_fmt)
        self.markPostDate = datetime.strptime(assignment['markPostDate'],
                                             config.date_fmt)
        events_api = self.api_server.event_get(self.course_id, self.assignment_id)
        self.completed_events = map(Event.factory_from_completed_event,
                                    events_api['eventList'])
        self.completed_events = sorted(self.completed_events,
                                       key=lambda x: x.state_number)

    def execute_state(self):
        last_event = max(self.completed_events, key=lambda x: x.dateRan)
        if last_event.repeatable and last_event.active_state():
            new_event = Event.factory(last_event.job)
            new_event.execute()
            api_server.event_create(
                new_event.assignmentID, new_event.summary, new_event.details,
                new_event.success, new_event.job)
        else:
            next_event= last_event.state_number + 1
            if next_event in events:
                new_event = Event.factory(events[next_event])
                if new_event.active_state():
                    new_event.execute()
            else:
                logger.info('LOG END OF ASSIGNMENT FLOW')
    def extract_next_event(self):
        pass

class Event:
    def __init__(self, state_number):
        self.state_number = state_number
    '''returns a boolean determining if the event is the current active
    state'''
    def active_state(self):
        pass
    def execute(self):
        print 'helo'
        pass
    def set_event(self, event):
        self.assignmentID = event['assignmentID']
        self.courseID = event['courseID']
        self.notificationID = event['notificationID']
        self.job = event['job']
        self.seen = event['seen']
        self.success = event['success']
        self.summary = event['summary']
        self.details = event['details']
        self.dateRan = datetime.strptime(event['dateRan'], config.date_fmt);

    @staticmethod
    def factory(event_type):
        vk_event= dict((v, k) for k, v in events.iteritems())

        if event_type == PeerMatchEvent.job:
            return PeerMatchEvent(vk_event[event_type])
        elif event_type == PeerMatchStragglersEvent.job:
            return PeerMatchStragglersEvent(vk_event[event_type])
        elif event_type == TaFillInReviewsEvent.job:
            return TaFillInReviewsEvent(vk_event[event_type])
        elif event_type  ==  GradingEvent.job:
            return GradingEvent(vk_event[event_type])

    @staticmethod
    def factory_from_completed_event(event):
        event_type = event['job']
        rev_event= dict((v, k) for k, v in events.iteritems())
        event_builder = None
        if event_type == PeerMatchEvent.job:
           event_builder = PeerMatchEvent(rev_event[event_type])
        elif event_type == PeerMatchStragglersEvent.job:
            event_builder = PeerMatchStragglersEvent(rev_event[event_type])
        elif event_type == TaFillInReviewsEvent.job:
            event_builder = TaFillInReviewsEvent(rev_event[event_type])
        elif event_type  ==  GradingEvent.job:
            event_builder = GradingEvent(rev_event[event_type])
        else:
            event_builder = Event(-1)
        event_builder.set_event(event)
        return event_builder


class PeerMatchEvent(Event):
    repeatable = False
    job = 'peer_match'
    def active_state(self, assignment):
        now = datetime.now()
        if assignment.submissionStopDate < now:
            return True
    def execute(self):
        pass
    def next(self):
        return events


class PeerMatchStragglersEvent(Event):
    repeatable = True
    repeat_interval = 60
    job = 'peer_match_stragglers'
    def active_state(self):
        pass
    def execute(self):
        pass

class TaFillInReviewsEvent(Event ):
    repeatable = False
    job = 'ta_fill_in_reviews'
    def active_state(self):
        pass
    def execute(self):
        pass

class GradingEvent(Event):
    repeatable = False
    job = 'grading'
    def active_state(self,):
        pass
    def execute(self):
        pass

events = {
    1: PeerMatchEvent.job,
    2: PeerMatchStragglersEvent.job,
    3: TaFillInReviewsEvent.job,
    4: GradingEvent.job
}
'''
events = {
            PeerMatchEvent.job: {'state_number': 1},
            PeerMatchStragglersEvent.job: {'state_number': 2},
            TaFillInReviewsEvent.job: { 'state_number': 3},
            GradingEvent.job: {'state_number': 4}
}
'''
if __name__=='__main__':
    c = api.server_accessor('http://enron.cs.northwestern.edu/~madhav/peermatch/mta/api/')
    e = EventAssignment(2,c)
    #e.getLastEvent();
#assume single direction to state machine
