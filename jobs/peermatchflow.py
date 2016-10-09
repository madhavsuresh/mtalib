from ..api.api import *
from ..algo.peer_assignment import *
from .. import config

c = config.api_server

def execute_peermatch_from_accessor(accessor,assignmentID, cover = [], load=3):
    
    peer_and_submission_ids = accessor.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
    subs = [(d['peerID'],d['submissionID']) for d in peer_and_submission_ids]
    exclude = {i:[j] for i,j in subs}

    (submissions,peers) = zip(*subs)
    peers = list(peers)
    submissions = list(submissions)
    
    assignments = assignment.peer_assignment_covered(peers, submissions, load, cover=cover, excludes=exclude)
    
    if assignment.peer_assignment_check(peers,assignments,exclude):
        return (assignments, cover)
    
    print 'error'
    return None

def execute_peermatch(assignmentID, cover=[], load=3):
  return execute_peermatch_from_accessor(c,assignmentID,cover,load)

  # this is old code.
  peer_and_submission_ids = c.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
  exclude = dict((x,[y,]) for x,y in [tuple(d.values()) for d in peer_and_submission_ids])
  submissions = [d['submissionID'] for d in peer_and_submission_ids]
  peers = [d['peerID'] for d in peer_and_submission_ids]
  assignments = peer_assignment_covered(peers, submissions, load, cover=cover, excludes=exclude)
  if peer_assignment_check(peers,assignments,exclude):
    return (assignments,cover)
  print 'error'
  return None


def matching_to_mechta_matching(matchings):
  pairs = kvs_to_pairs(matchings)
  return [{'reviewerID': i, 'submissionID': j} for i,j in pairs]


def insert_peermatch(assignmentID):
  (assignments,cover) = execute_peermatch(assignmentID)
  mechta_matching = matching_to_mechta_matching(assignments)
  c.peermatch_create_bulk(assignmentID, mechta_matching)
  return cover

def insert_ta_matches_from_accessor(accessor,assignmentID, cover):
  courseID = int(accessor.get_courseID_from_assignmentID(assignmentID)['courseID'])
  taIDs = accessor.get_tas_from_course(courseID)['taIDs']
  matching = random_assignment(taIDs, cover)
  mechta_matching = matching_to_mechta_matching(matching)
  return accessor.peermatch_create_bulk(assignmentID, mechta_matching)


def insert_ta_matches(assignmentID, cover):
  return insert_ta_matches_from_accessor(c,assignmentID, cover)


def execute(assignmentID):
    cover = insert_peermatch(assignmentID)
    insert_ta_matches(assignmentID,cover)
