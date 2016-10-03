from api.api import *
from algo.peer_assignment import *
import config
c = config.api_server

def execute_peermatch(assignmentID, cover=[], load=3):
  peer_and_submission_ids = c.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
  exclude = dict((x,[y,]) for x,y in [tuple(d.values()) for d in peer_and_submission_ids])
  submissions = [d['submissionID'] for d in peer_and_submission_ids]
  peers = [d['peerID'] for d in peer_and_submission_ids]
  assignments = peer_assignment_covered(peers, submissions, load, cover=cover, excludes=exclude)
  if peer_assignment_check(peers,assignments,exclude):
    return {'assignments': assignments, 'cover': cover}
  print 'error'
  return None

def convert_alg_to_api_matching(matchings):
  peer_matchings_api_fmt = []
  for peerID, submissionIDs in matchings.iteritems():
    for submissionID in submissionIDs:
      peer_matchings_api_fmt.append({"reviewerID": peerID, "submissionID": submissionID})
  return peer_matchings_api_fmt

def insert_peermatch(assignmentID):
  assignments_and_cover = execute_peermatch(assignmentID)
  assignments = assignments_and_cover['assignments']
  cover = assignments_and_cover['cover']
  peer_assignments_api_fmt = convert_alg_to_api_matching(assignments)
  c.peermatch_create_bulk(assignmentID, peer_assignments_api_fmt)
  return cover

def insert_ta_matches(assignmentID, cover):
  courseID = int(c.get_courseID_from_assignmentID(assignmentID)['courseID'])
  taIDs = c.get_tas_from_course(courseID)['taIDs']
  n = len(taIDs)
  m = len(cover)
  matching = random_ta_assignment(taIDs, cover)
  matching_api_fmt = convert_alg_to_api_matching(matching)
  c.peermatch_create_bulk(assignmentID, matching_api_fmt)

def execute(assignmentID):
    cover = insert_peermatch(assignmentID)
    insert_ta_matches(assignmentID,cover)
