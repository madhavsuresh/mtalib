from ..api.api import *
from ..algo import peer_assignment as assignment
from ..jobs import grading
import random
from ..algo.util import *
import logging
from pprint import pprint
from copy import deepcopy



logger = logging.getLogger()


job_name = 'match'
job_summary = 'Matching Submissions to Peers and TAs'

    
default_params = {'ta_load': 10,
                  'peer_load': 3,
                  'tas':None}


def run(accessor,assignmentID,courseID=None,**params):
    if not courseID:
        courseID = accessor.get_courseID(assignmentID)


    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID=courseID)
    d_params.update(a_params)
    params = d_params



    ta_load = params['ta_load']
    peer_load = params['peer_load']
    tas = params['tas']
    if not tas:
        tas = accessor.get_tas_from_course(courseID=courseID,markingLoad=1)


    logger.info("Executing peer match with peer load %d and ta load %d and tas %s",peer_load,ta_load,tas)

    subs = accessor.get_student_and_submission_ids(assignmentID,courseID=courseID)

    excludes = {i:[j] for i,j in subs}

    (peers,submissions) = zip(*subs)
    peers = list(peers)
    submissions = list(set(submissions))

    students = accessor.get_students(courseID=courseID)


    (matching,cover) = peermatch_simple(students,submissions,k=peer_load,excludes=excludes,cover_size = ta_load)


    if matching:
        pprint(matching)
        insert_matching_from_accessor(accessor,assignmentID,matching,courseID=courseID)

    if not matching:
        logger.error("Failed to find matching.  Rerun.")
        return False

    if cover:
        insert_ta_matches_from_accessor(accessor,assignmentID, cover, tas = tas,courseID=courseID)




    return True

    

    
    


def get_tas_for_assignment(accessor,assignmentID,ta_matching=[]):

    # find which TA to grade this.
    tas = []
    assignment_name = accessor.get_assignment(assignmentIDs = [assignmentID])[0]['name']

    if ta_matching:
        tas =  [ta for (ta,hw) in kvs_to_pairs(ta_matching) if hw in assignment_name]
        logger.info("Matching \'%s\' to TAs %s",assignment_name,str(tas))
    if not tas:
        tas = accessor.get_tas_from_course(markingLoad=1)
        logger.info("No TA assignment for \'%s\', assigning to all TAs.",
                    assignment_name)

    return tas




def get_excludes(accessor,assignmentID):

    subs = accessor.get_student_and_submission_ids(assignmentID)
    exclude = {i:[j] for i,j in subs}

    return exclude

def execute_peermatch_original_from_accessor(accessor,assignmentID, cover = None, load=3):
    if cover == None:
        cover = []

    subs = accessor.get_student_and_submission_ids(assignmentID)

    exclude = {i:[j] for i,j in subs}


    (peers,submissions) = zip(*subs)
    submissions = list(set(submission))

    peers = list(peers)
    submissions = list(submissions)


    assignments = assignment.peer_assignment_covered(peers, submissions, load, cover=cover, excludes=exclude)
    
    if assignment.peer_assignment_check(peers,assignments,cover,exclude):
        return (assignments, cover)
    
    logger.error("peer assignment failed check, aborting")
    return (None,None)

def execute_peermatch_original(assignmentID, cover=None, load=3):
  return execute_peermatch_from_accessor(c,assignmentID=assignmentID,cover=cover,load=load)


def mechta_matching_to_matching(mechta_matchings):
  return [(d['reviewerID'],d['submissionID']) for d in mechta_matchings]



def matching_to_mechta_matching(matchings):
  pairs = ensure_pairs(matchings)
  return [{'reviewerID': i, 'submissionID': j} for i,j in pairs]


def insert_matching_from_accessor(accessor,assignmentID,matching,courseID=None):

  mechta_matching = matching_to_mechta_matching(matching)

  random.shuffle(mechta_matching)  # make sure the cover is random in the peers ordering.
  logger.info("assigning %s reviews to %s users.",len([j for js in matching.values() for j in js]),len(matching.keys()))
  return accessor.peermatch_create_bulk(assignmentID, mechta_matching)
  

def insert_peermatch_from_accessor(accessor,assignmentID):
  (assignments,cover) = execute_peermatch_from_accessor(accessor,assignmentID)
  
  logger.info('adding peer match')
  insert_matching_from_accessor(accessor,assignmentID,assignments)
  
  return cover

def insert_peermatch(assignmentID):
    return insert_peermatch_from_accessor(c,assignmentID)

def insert_matches_from_accessor(accessor,assignmentID, user, subs,courseID=None):

    matching = {user: subs}

    logger.info('matching user %d to submissions %s',user,str(subs))

    return insert_matching_from_accessor(accessor,assignmentID,matching)



def insert_ta_matches_from_accessor(accessor,assignmentID, cover, tas = None,courseID=None):
    # if no tas are listed, get them from the class, and assign to all.
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    if not tas:
        tas = accessor.get_tas_from_course(courseID,markingLoad=1)
            
    matching = assignment.random_assignment(tas, cover)

    logger.info('adding ta matching')
    return insert_matching_from_accessor(accessor,assignmentID,matching)


def get_nonsubmitters(accessor,assignmentID):
    users = accessor.get_users()
    tas = accessor.get_tas_from_course(markingLoad=-1)
    submitters = accessor.peermatch_get_peer_ids(assignmentID)
    submissions = accessor.peermatch_get_submission_ids(assignmentID)
    nonsubmitters = list(set(users) - set(tas) - set(submitters))
    
    return(nonsubmitters)

# Input: recent: how many assignments to go back to see if a user is active.
# Algorithm:
#   - gets active users who did not submit.
#   - gets the cover (submissions to be reviewed by TAs)
#   - assigns users to cover (1to1).
#   - assigns users to other submissions (2toL).
def assign_reviews_to_nonsubmitters(accessor,assignmentID,recent=4):
    active_users = get_active_users(accessor,assignmentID)
    tas = accessor.get_tas_from_course()
    submitters = accessor.peermatch_get_peer_ids(assignmentID)
    submissions = accessor.peermatch_get_submission_ids(assignmentID)
    nonsubmitters = list(set(active_users) - set(tas) - set(submitters))
    logger.info("Non-submitters: %s", nonsubmitters)


    cov = cover.get_cover_from_accessor(accessor,assignmentID)
    originalcover = copy(cov)

    assignments = peer_assignment_covered(nonsubmitters,submissions,3,cov)

    if set(cov) == set(originalcover):
        logger.info("original cover is sufficient")
        mechta_matching = matching_to_mechta_matching(assignments)
        logger.info("assigning %s peer reviews to %s peers.",len([j for js in assignments.values() for j in js]),len(assignments.keys()))
        accessor.peermatch_create_bulk(assignmentID, mechta_matching)
    else:
        logger.warn("original cover not sufficient. no additional reviews added.")

    return assignments



def insert_ta_matches(assignmentID, cover):
  return insert_ta_matches_from_accessor(c,assignmentID, cover)


def execute_from_accessor(accessor,assignmentID,k=3,cover_size=40):
    (assn,cov) = peermatch_from_accessor(accessor,assignmentID,k=k,cover_size=cover_size)
    insert_matching_from_accessor(accessor,assignmentID,assn)
    insert_ta_matches_from_accessor(accessor,assignmentID,cov)

    return (assn,cov)

def execute(assignmentID,k=3,cover_size=40):
    return execute_from_accessor(c,assignmentID,k=k,cover_size=cover_size)


# gets users who are probably active to for a given assignment.
# goes back and looks at 'recent' assignments.
def get_active_peers(accessor,assignmentID,recent=4):
    assignments = range(max(assignmentID-recent,0),assignmentID)
    
    students = set()
    for assn in assignments:
        submitters = accessor.peermatch_get_peer_ids(assn)
        students |= set(submitters)
        
    return list(students)


# average peer review grades for assignments 1...assignmentID
# returns {peer:avg_review_grade,...}
def review_grade_tallies(accessor,assignmentID):
    courseID = accessor.get_courseID(assignmentID)
    tas = grading.tas_from_accessor(accessor,courseID)

    agrades = {}
    for assn in range(1,assignmentID+1):

        print "CALCULATING REVIEW GRADES FOR ASSIGNMENT: " + str(assn)
        reviews = grading.reviews_from_accessor(accessor,assn)
        truths = grading.truths_from_reviews(reviews,tas)
        weights = accessor.get_rubric_weights(assn)

        agrades[assn] = grading.grade_peers(reviews,truths,weights,skip_loss=0.5)

    # igrades: {i:{assn:grade,...},...}
    igrades = kkv_invert(agrades)

    grades = {int(i): avg(atog.values()) for i,atog in igrades.items() }
    return grades

# sort peers by grades.
def sorted_peers(peers,grades):
    return sorted(peers,key=lambda i:grades.get(i,0.0),reverse=True)
    

# Algorithm:
#    - get all peers.
#    - get submissions.
#    - sort peers by qualities.
#    - call peer_match
# return peer review assignment and cover
def peermatch_from_accessor(accessor,assignmentID,k=3,cover_size=None):
    
    peer_and_submission_ids = accessor.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
    subs = [(d['peerID'],d['submissionID']) for d in peer_and_submission_ids]
    exclude = {i:[j] for i,j in subs}

    (peers,submissions) = zip(*subs)
    peers = list(peers)
    submissions = list(submissions)

    tally_assignmentID = ((assignmentID-3) // 2) * 2
    print "tally assignmentID: " + str(tally_assignmentID)
    
    grades = review_grade_tallies(accessor,tally_assignmentID)
    
    peers = sorted_peers(peers,grades)
    onehundred = min(100,len(peers)-1)
    print "quality of peer " + str(onehundred)+ ": " + str(grades.get(peers[onehundred],0.0))
    
    # add nonsubmitters to the end of the list.
    all_users = get_active_peers(accessor,assignmentID)
    nonsubmitters = list(set(all_users) - set(peers))
    print "adding " + str(len(nonsubmitters)) + " nonsubmitters"
    peers = peers + nonsubmitters
    
    (assignments,cover) = peermatch(peers,submissions,k,exclude,cover_size)
    
    if assignment.peer_assignment_check(peers,assignments,cover,exclude):
        logger.info("peer assignment is good, cover is good")


        return (assignments, cover)
    
    logger.error("peer assignment failed check, aborting")
    return None

# This creates a peer match.
# Input:
#   peers: list of peers, sorted by quality.
# Output:
#   assignments: {i:[j,...],...}
#   cover: [j,...]
# Algorithm:
#   0. randomize the submissions.
#   1. match peers to cover.
#   2. calculate how many remaining submissions have 2 and 3 reviews.
#   3. for the remaining submissions with 2 reviews, 
#      find a 2to2 matching of the highest quality peers.
#   4. for the remaining submissions with 3 reviews,
#      find a 2to2 matching of the middle quality peers.
#   5. add the lowest quality peers to (4)  
def peermatch(peers,subs,k=3,excludes={},cover_size = None):

    # flesh out excludes
    excludes = {p : (excludes[p] if p in excludes else []) for p in peers}

    n = len(peers)
    m = len(subs)

    # set cover to evenly distribute if not specified.
    if not cover_size:
        cover_size = math.ceil(m / k)
    cover_size = min(cover_size,len(subs))

    cover = random.sample(subs,cover_size)
    remaining = list(set(subs)-set(cover))
    random.shuffle(remaining)
    
    # assign cover.
    print "ASSIGNING ALL " + str(n) + " PEERS TO COVER OF SIZE " + str(cover_size)

    cover_assignments = assignment.peer_assignment(peers,cover,1,excludes)
    
    # add cover_assignment to excludes.
    excludes = {p: excludes[p] + cover_assignments[p] for p in peers}

    

    k -= 1             # remaining assignments per peer.
    m = len(remaining) # remaining submissions.
    
    if m is 0:
        return (cover_assignments,cover)

    l = n * k // m     # reviews per submission rounded down.
    x = (n * k) % m    # submissions with extra reviews
    mm = m - x         # submissions with l (ell) reviews
    nn = (mm * l + k-1) // k    # this is: m * l / k rounded up.
    
    
    print "peer load: " + str(k)
    print "submission load: " + str(l)
    print "submissions at load: " + str(mm)
    print "peers at load: " + str(nn)
    print "submissions at load+1: " + str(x)
    
    
    # strategy: match top to mm, match bottom to x.
    
    # split submissions to top and bottom
    top_subs = remaining[:mm]
    bottom_subs = remaining[mm:]
    
    #split to peers to top and bottom.
    top_peers = peers[:nn]
    bottom_peers = peers[nn:]
    
    
    

    # assign top to remaining submissions.
    print "ASSIGNING TOP " + str(len(top_peers)) + " PEERS TO " + str(len(top_subs)) + " SUBMISSIONS" 
    top_assignments = assignment.peer_assignment(top_peers,top_subs,k,excludes)
    
    # assign bottom to remaining submissions.
    # do 2-to-2 matching of middle
    middle_peers = bottom_peers[:len(bottom_subs)]
    bottom_peers = bottom_peers[len(bottom_subs):]
    print "ASSIGNING MIDDLE " + str(len(middle_peers)) + " PEERS TO " + str(len(bottom_subs)) + " SUBMISSIONS" 
    middle_assignments = assignment.peer_assignment(middle_peers,bottom_subs,k,excludes)
    print "ASSIGNING BOTTOM " + str(len(bottom_peers)) + " PEERS TO " + str(len(bottom_subs)) + " SUBMISSIONS" 
    bottom_assignments = assignment.peer_assignment(bottom_peers,bottom_subs,k,excludes)
    
    # combine (note: peers are disjoint)
    top_assignments.update(bottom_assignments)
    top_assignments.update(middle_assignments)
    
    # combine cover and residual assignment
    assignments = {p: cover_assignments[p] + top_assignments[p] for p in peers}

    return assignments,cover


# This creates a peer match.
# Input:
#   peers: list of peers, sorted by quality.
# Output:
#   assignments: {i:[j,...],...}
#   cover: [j,...]
# Algorithm:
#   0. randomize the submissions.
#   1. match peers to cover.
#   2. match peers to remaining submissions.
def peermatch_simple(peers,subs,k=3,excludes={},cover_size = None):


    # flesh out excludes
    excludes = {p : (excludes[p] if p in excludes else []) for p in peers}

    n = len(peers)
    m = len(subs)

    # set cover to evenly distribute if not specified.
    if not cover_size:
        cover_size = math.ceil(m / k)
    cover_size = min(cover_size,len(subs))

    cover = random.sample(subs,cover_size)
    remaining = list(set(subs)-set(cover))
    random.shuffle(remaining)
    
    # assign cover.
    logger.info("ASSIGNING ALL " + str(n) + " PEERS TO COVER OF SIZE " + str(cover_size))

    cover_assignments = assignment.peer_assignment(peers,cover,1,excludes)
    
    # add cover_assignment to excludes.
    excludes = {p: excludes[p] + cover_assignments[p] for p in peers}

    k -= 1             # remaining assignments per peer.
    m = len(remaining) # remaining submissions.

    if m is 0:
        return (cover_assignments,cover)

    
    # assign top to remaining submissions.
    logger.info("ASSIGNING ALL %d PEERS TO REMAINING %d SUBMISSIONS (%d EACH)",n,m,k)
    remaining_assignments = assignment.peer_assignment(peers,remaining,k,excludes)

    # process failed, need to rerun.
    if not remaining_assignments:
        return ({},[])

    # combine cover and residual assignment
    assignments = {p: cover_assignments[p] + remaining_assignments[p] for p in peers}

    return assignments,cover



def missing_review_matchids(accessor, assignmentID, tas=None, courseID=None):
    courseID = accessor.get_courseID(assignmentID,courseID=courseID)
    mta_reviews = grading.mechta_reviews_from_accessor(accessor,assignmentID,courseID=courseID)
    matchids = ensure_kkv(grading.mechta_reviews_to_matchids(mta_reviews))

    missing = ensure_pairs(grading.missing_truths_from_accessor(accessor,assignmentID,tas=tas,courseID=courseID))
    print "MISSING REVIEWS"
    pprint(missing)
    
    matchIDs = sorted([int(matchids[i][j]) for (i,j) in missing]) 

    return matchIDs
