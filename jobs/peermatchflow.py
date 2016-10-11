from ..api.api import *
from ..algo import peer_assignment as assignment
from .. import config
from ..algo.util import *
import logging

logger = logging.getLogger()

c = config.api_server

def execute_peermatch_from_accessor(accessor,assignmentID, cover = None, load=3):
    if cover == None:
        cover = []
    peer_and_submission_ids = accessor.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
    subs = [(d['peerID'],d['submissionID']) for d in peer_and_submission_ids]
    exclude = {i:[j] for i,j in subs}

    (peers,submissions) = zip(*subs)
    peers = list(peers)
    submissions = list(submissions)

    

    assignments = assignment.peer_assignment_covered(peers, submissions, load, cover=cover, excludes=exclude)
    
    if assignment.peer_assignment_check(peers,assignments,cover,exclude):
        return (assignments, cover)
    
    logger.error("peer assignment failed check, aborting")
    return None

def execute_peermatch(assignmentID, cover=None, load=3):
  return execute_peermatch_from_accessor(c,assignmentID=assignmentID,cover=cover,load=load)



def matching_to_mechta_matching(matchings):
  pairs = ensure_pairs(matchings)
  return [{'reviewerID': i, 'submissionID': j} for i,j in pairs]

def insert_peermatch_from_accessor(accessor,assignmentID):
  (assignments,cover) = execute_peermatch_from_accessor(accessor,assignmentID)
  mechta_matching = matching_to_mechta_matching(assignments)
  logger.warn("assigning %s peer reviews to %s peers.",len([j for js in assignments.values() for j in js]),len(assignments.keys()))
  accessor.peermatch_create_bulk(assignmentID, mechta_matching)
  return cover

def insert_peermatch(assignmentID):
    return insert_peermatch_from_accessor(c,assignmentID)

def insert_ta_matches_from_accessor(accessor,assignmentID, cover):
  courseID = int(accessor.get_courseID_from_assignmentID(assignmentID)['courseID'])
  taIDs = accessor.get_tas_from_course(courseID)['taIDs']
  matching = assignment.random_assignment(taIDs, cover)
  mechta_matching = matching_to_mechta_matching(matching)
  logger.warn("assigning %d reviews to %d tas",len(cover),len(taIDs))
  return accessor.peermatch_create_bulk(assignmentID, mechta_matching)


def insert_ta_matches(assignmentID, cover):
  return insert_ta_matches_from_accessor(c,assignmentID, cover)


def execute_from_accessor(accessor,assignmentID):
    cover = insert_peermatch_from_accessor(accessor,assignmentID)
    insert_ta_matches_from_accessor(accessor,assignmentID,cover)

def execute(assignmentID):
    return execute_from_accessor(c,assignmentID)
