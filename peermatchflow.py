from python_lib.mta.api import *
from simulations.Python.peer_review_lib import *

c = server_accessor('http://enron.cs.northwestern.edu/~madhav/peermatch/mta/api/')

def execute_peermatch(assignmentID, cover=[], load=3):
  c = server_accessor('http://enron.cs.northwestern.edu/~madhav/peermatch/mta/api/')
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
  #assignments_api_fmt = [{'reviewerID': x, 'submissionID': y} for (x,y) in 
  peer_assignments_api_fmt = convert_alg_to_api_matching(assignments)
  #request_object = {'peerMatches': assignments_api_fmt, 'assignmentID': assignmentID}
  c.peermatch_create_bulk(assignmentID, peer_assignments_api_fmt)
  return cover

def insert_ta_matches(assignmentID, cover):
  courseID = int(c.get_courseID_from_assignmentID(assignmentID)['courseID'])
  print type(courseID)
  taIDs = c.get_tas_from_course(courseID)['taIDs']
  n = len(taIDs)
  m = len(cover)
  matching = peer_assignment(taIDs, cover, m/n)
  matching_api_fmt = convert_alg_to_api_matching(matching)
  c.peermatch_create_bulk(assignmentID, matching_api_fmt)

  
cover = insert_peermatch(1)
insert_ta_matches(1,cover)

