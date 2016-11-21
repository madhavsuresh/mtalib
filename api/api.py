import requests, json, string, pprint, pytz, calendar, time
from datetime import datetime, timedelta
from pytz import timezone
from requests.auth import HTTPBasicAuth
from copy import copy, deepcopy
#import config


class server_accessor:
  """Class for accessing the Mechanical TA API"""
  server_url = ''
  timezone = ''
  date_fmt = ''
  courseID = None

  def __init__(self, p_server_url, course_id = 1, local_timezone = 'US/Central', date_fmt = '%m/%d/%Y %H:%M:%S', username='', password=''):
    """Creates a server_accessor instance. Required param: p_server_url - MechTA instance API url. Optional params: local_timezone - pytz formatted timezone (default value: US/Central), date_fmt - string format for passed in dates (default value: '%m/%d/%Y %H:%M:%S')"""
    if p_server_url[-1:] != '/':
      p_server_url += '/'
    self.server_url = p_server_url;
    self.timezone = timezone(local_timezone)
    self.date_fmt = date_fmt
    self.courseID = course_id
    self.username = username
    self.password = password

  def __str__(self):
    """Prints the url this instance is accessing"""
    return self.server_url

  def server_get(self, endpoint, params):
      r = requests.get(self.server_url + endpoint, data=json.dumps(params), 
              auth=(self.username, self.password))
      return r

  def server_post(self, endpoint, params):
      r = requests.post(self.server_url + endpoint, data=json.dumps(params), 
              auth=(self.username, self.password))
      return r

  def check_connection(self,courseID=None):
    if courseID == None:
      courseID = self.courseID
    # would be better to ping a specific endpoint to check the connection.
    r = self.server_get('user/get_tas_from_courseid', {'courseID':courseID})
    return r.status_code == requests.codes.ok


  ############################ COURSE ###########################

  def create_course(self, name, displayName, authType='pdo', registrationType='Open', browsable=True):
    """Creates a course with optional values. name and displayName are required parameters and name must be unique for call to not return error"""
    course_params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    del course_params['self']
    return requests.post(self.server_url + 'course/create', data=json.dumps(course_params))

  def update_course(self, courseID = None, name='', displayName='', authType='', registrationType='', browsable=''):
    """Updates course specified by courseID with any additional optional parameters specified by user"""
    if courseID == None:
        courseID = self.courseID
    params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    del params['self']
    course_params = {key:value for (key, value) in params.iteritems() if value}

    return requests.post(self.server_url + 'course/update', data=json.dumps(course_params))

  def delete_course(self, courseID = None):
    """Deletes the course specified by ID"""
    if courseID == None:
        courseID = self.courseID
    delete_data = {'courseID' : courseID}
    return requests.post(self.server_url + 'course/delete', data=json.dumps(delete_data))

  def get_course(self, courseID=""):
    """If a courseID is supplied this returns the information associated with that class, without a specified courseID this returns a list of courses with courseID, name, displayName and browsable values for each course"""
    get_data = {}
    if courseID:
      get_data['courseID'] = courseID
    return requests.get(self.server_url + 'course/get', data=json.dumps(get_data))

  ############################ USERS ###########################

  def create_users(self, list_of_users, course_id = None):
    """Accepts a courseID and a list of user dictionaries and creates the given users under that course"""
    if course_id == None:
        course_id = self.courseID
    create_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/create', data = json.dumps(create_data))

  def update_users(self, list_of_users, course_id = None):
    """Accepts a courseID and a list of user dictionaries and updates the given users under that course"""
    if course_id == None:
        course_id = self.courseID
    update_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/update', data = json.dumps(update_data))

  def delete_users(self, list_of_users, courseID = None):
    """Accepts a courseID and a list of usernames and drops the given users under that course"""
    if courseID == None:
        courseID = self.courseID
    delete_data = {'courseID' : courseID, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/delete', data = json.dumps(delete_data))

  def get_users(self, courseID = None, users=""):
    """Accepts a courseID and an optional list of usernames. Without the list of usernames this returns a list of users by username in the given course, with the optional list this returns more detailed info on each given username"""
    if courseID == None:
        courseID = self.courseID
    data = locals()
    del data['self']
    if not users:
      del data['users']
    return self.server_get('user/get',data).json()

  def get_tas_from_course(self, courseID):
    params = {'courseID': courseID}
    r = self.server_get('user/get_tas_from_courseid', params)
    return r.json()

  ################################## Assignments ######################################

  def create_assignment(self, name, submissionQuestion, submissionStartDate = 1472352458, submissionStopDate = 2472352458, reviewStartDate = 1472352458, reviewStopDate = 2472352458, markPostDate = 2472352458, appealStopDate = 2472352458, courseID = None, day_offset = 0, maxSubmissionScore = 10, maxReviewScore = 5, defaultNumberOfReviews = 3, submissionType = 'essay'):
    """Creates an assignment based on the passed in parameters and on hardcoded defaults. Accepts either Unix epoch time or local time in format specified by constructor. Date parameters - [submissionStartDate, submissionStopDate, reviewStartDate, reviewStopDate, markPostDate, appealStopDate]. Also accepts a time offset in days."""
    if courseID == None:
        courseID = self.courseID
    assignment_params = locals()
    del assignment_params['self']

    defaults = {'password' : 'null', 
                'passwordMessage' : 'null', 
                'visibleToStudents' : 1, 
                'assignmentType' : 'peerreview', 
                'dateFormat' : 'MMMM Do YYYY, HH:mm', 
                'calibrationPoolAssignmentIds' : [], 
                'extraCalibrations' : 0, 
                'calibrationStartDate' : 0, 
                'calibrationStopDate' : 0, 
                'showMarksForReviewsReceived' : 1, 
                'showOtherReviewsByStudents' : 0, 
                'showOtherReviewsByInstructors' : 0, 
                'showMarksForOtherReviews' : 0, 
                'showMarksForReviewedSubmissions' : 0, 
                'showPoolStatus' : 0, 
                'calibrationMinCount' : 0, 
                'calibrationMaxScore' : 0, 
                'calibrationThresholdMSE' : 0, 
                'calibrationThresholdScore' : 0, 
                'allowRequestOfReviews' : 0, 
                'submissionSettings' 
                   : {'topics' : [], 'autoAssignEssayTopic' : 1, 'essayWordLimit' : 10000}
                }

    defaults.update(assignment_params)
    self.convert_assignment_datetimes_to_unix_time(defaults)
    if day_offset:
      self.add_day_offset(day_offset, defaults)
    return requests.post(self.server_url + 'assignment/create', data = json.dumps(defaults))

  def update_assignment(self, name, submissionQuestion, submissionStartDate = 1472352458, submissionStopDate = 2472352458, reviewStartDate = 1472352458, reviewStopDate = 2472352458, markPostDate = 2472352458, appealStopDate = 2472352458, courseID = None, day_offset = 0, maxSubmissionScore = 10, maxReviewScore = 5, defaultNumberOfReviews = 3, submissionType = 'essay'):
    """Updates an assignment based on the passed in parameters and on hardcoded defaults. Accepts either Unix epoch time or local time in format specified by constructor."""
    if courseID == None:
        courseID = self.courseID
    assignment_params = locals()
    del assignment_params['self']
    defaults = {'password' : 'null', 'passwordMessage' : 'null', 'visibleToStudents' : 1, 'assignmentType' : 'peerreview', 'dateFormat' : 'MMMM Do YYYY, HH:mm', 'calibrationPoolAssignmentIds' : [], 'extraCalibrations' : 0, 'calibrationStartDate' : 0, 'calibrationStopDate' : 0, 'showMarksForReviewsReceived' : 1, 'showOtherReviewsByStudents' : 0, 'showOtherReviewsByInstructors' : 0, 'showMarksForOtherReviews' : 0, 'showMarksForReviewedSubmissions' : 0, 'showPoolStatus' : 0, 'calibrationMinCount' : 0,'calibrationMaxScore' : 0,'calibrationThresholdMSE' : 0,'calibrationThresholdScore' : 0, 'allowRequestOfReviews' : 0, 'submissionSettings' : {'topics' : [], 'autoAssignEssayTopic' : 1, 'essayWordLimit' : 10000}}

    defaults.update(assignment_params)
    self.convert_assignment_datetimes_to_unix_time(defaults)
    if day_offset:
      self.add_day_offset(day_offset, defaults)
    return requests.post(self.server_url + 'assignment/update', data = json.dumps(assignment_params))

  def get_assignment(self, assignmentIDs, courseID = None):
    """Takes a courseID and a list of assignmentIDs and returns the information of the given assignments"""
    if courseID == None:
        courseID = self.courseID
    assignment_params = locals()
    del assignment_params['self']
    print assignment_params
    return requests.get(self.server_url + 'assignment/get', data = json.dumps(assignment_params))

  def get_courseID_from_assignmentID(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('assignment/courseID_from_assignmentID', params)

    return r.json()


  # THIS ENDPOINT HAS NOT BEEN IMPLEMENTED.
  def get_assignment_event(self, courseID, assignmentID=None):
      if assignmentID:
          params = {'courseID': courseID, 'assignmentID': assignmentID}
      else:
          params = {'courseID': courseID}

      r = self.server_get('assignment/get_all_from_course',params)
      return r.text

  ################################## Rubrics ##########################################

  rubric_question_defaults = {
    'name':'Default question', 
    'question':'Default question text.', 
    'hidden':0, 
    'displayPriority':0, 
    'weight':10,
    'options':   [{'label' : '10' , 'score' : 1.0}, 
                  {'label' : '9' , 'score' : 0.9}, 
                  {'label' : '8' , 'score' : 0.8}, 
                  {'label' : '7' , 'score' : 0.7}, 
                  {'label' : '6' , 'score' : 0.6}, 
                  {'label' : '5' , 'score' : 0.5}, 
                  {'label' : '4' , 'score' : 0.4}, 
                  {'label' : '3' , 'score' : 0.3}, 
                  {'label' : '2' , 'score' : 0.2}, 
                  {'label' : '1' , 'score' : 0.1}, 
                  {'label' : '0' , 'score' : 0.0},                   
                  {'label' : 'Skip', 'score' : -0.1}]    
  }

  def create_rubric_question(self, assignmentID, courseID = None, defaults=rubric_question_defaults,**kwargs):
    """Creates rubric for given courseID and assignmentID with given name"""

    if courseID == None:
      courseID = self.courseID

    params = copy(defaults)
    params.update(kwargs)
    params['assignmentID'] = assignmentID
    params['courseID'] = courseID


    weight = params['weight']
    del params['weight']

    # scores can be normalized, and then reweighted by weight.
    # need to store reweighted scored in MTA.
    options = params['options'] = copy(params['options'])
    for o in options:
      o['score'] *= weight


    return self.server_post('rubric/create', params)

## UPDATE_RUBRIC
##   - allows partial update.
## NOTE: cannot set 'displayPriority' = 0.  Any other integers work.  This is
##   due to an issue with the MechTA backend for compatibility with the UI where
##   updates from the UI which are not intended to update displayPriority
##   set displayPriority=0.  To ignore those, we have to ignore them all.
  def update_rubric_question(self, assignmentID, questionID, courseID = None, **kwargs):
    """Creates rubric for given courseID and assignmentID with given name"""

    if courseID == None:
        courseID = self.courseID
    
    # get new parameters.
    new_params = locals()
    new_params.update(kwargs)
    del new_params['self']
    del new_params['kwargs']

    # get old parameters
    rubrics = self.get_rubric(assignmentID)
    params = rubrics[questionID]

    params.update(new_params)
    
    # scores can be normalized, and then reweighted by weight.
    # need to store reweighted scored in MTA.
    if 'options' in params:
      for o in params['options']:
        o['score'] *= params['weight']   
    
    if 'weight' in params:
      del params['weight']

    return self.server_post('rubric/update', params)

## GET_RUBRICS
##    - returns *dictionary* of rubrics: {questionID:rubric,...}
##    - scores are floating point, normalized to have maximum score = 1.0
##    - 'weight'field is added (the original maximum score)
##
  def get_rubric(self, assignmentID):
    '''Gets all rubrics right now based on AssignmentID '''
    assignment_params = locals()
    del assignment_params['self']
    
    req = self.server_get('rubric/get', assignment_params)
    questions = req.json()
    
    # make questionIDs ints
    # THIS SHUOLD HAPPEN IN THE API ENDPOINT BUT DOES NOT.
    ids = [q['questionID'] for q in questions]
    for i in ids:
        i['id'] = int(i['id'])
    
    # normalize weights    
    for q in questions:

        # make scores into numbers.
        if 'options' in q:
        
            # make sure score is a number
            for o in q['options']:
                o['score'] = float(o['score'])
      
            # calculate max, normalize, and set weight.
            weight = max([o['score'] for o in q['options']])
            for o in q['options']:
                o['score'] /= weight

            q['weight'] = weight
    
    rubric = {q['questionID']['id']:q for q in questions}
    
    return rubric

  def get_rubric_weights(self,assignmentID):
    '''Gets rubric weights into dictionary {q:weight,...}'''
    rubric = self.get_rubric(assignmentID)

    # question weights: {q:weight,...}
    weights = {q:props['weight'] for q,props in rubric.items() if 'weight' in props}
 
    return weights


  ############################### APPEALS ##############################
  def get_appeals(self):
      r = self.server_get('appeals/get', None);
      return r.json()['appeals']

  def get_unresolved_appeals(self):
      all_appeals = self.get_appeals()
      unresolved_appeals = filter(lambda x: x['appealType'] != 'resolvedAppeal', all_appeals)
      return unresolved_appeals

  def get_resolved_appeals(self):
      all_appeals = self.get_appeals()
      resolved_appeals = filter(lambda x: x['appealType'] == 'resolvedAppeal', all_appeals)
      return resolved_appeals

  def get_resolved_appeals_by_assignment(self, assignmentID):
      all_appeals = self.get_resolved_appeals()
      matches_for_assignment = self.peermatch_get(assignmentID)
      matchIDs = [match['matchID'] for match in matches_for_assignment] 
      appeals_for_assignment = filter(lambda x: x['matchID'] in matchIDs  , all_appeals)
      return appeals_for_assignment

  def get_unresolved_appeals_by_assignment(self, assignmentID):
      all_appeals = self.get_unresolved_appeals()
      matches_for_assignment = self.peermatch_get(assignmentID)
      matchIDs = [match['matchID'] for match in matches_for_assignment] 
      appeals_for_assignment = filter(lambda x: x['matchID'] in matchIDs  , all_appeals)
      return appeals_for_assignment
  
  def set_appeal_as_resolved(self, appealMessageID):
      params = {'appealMessageID': appealMessageID}
      r =  self.server_post('/appeals/set_as_resolved', params)
      return r.text

  def create_appeal_type(self, appealType):
      params = {'appealType': appealType}
      r = self.server_post('/appeals/create_appeal_type', params)
      return r.text
             

  ############################### GRADES ##############################

  def set_grades(self,assignmentID, grades, courseID = None):
    """Sets grades for a given assignmentID under the given course using the passed in list of (submissionID, grades) tuples"""
    if courseID == None:
        courseID = self.courseID
    grades_params = locals()
    del grades_params['self']
    r = self.server_post('grades/create', grades_params)
    return r

  def get_submission_grades(self):
     r = self.server_get('grades/submissions', None);
     return r.json()['scores']

  def get_peerreview_grades(self):
     r = self.server_get('grades/peerreviews', None);
     return r.json()['scores']

################################ PEERMATCH ################################
  def peermatch_create(self, assignmentID, submissionID, reviewerID):
    params = {'assignmentID': assignmentID, 'peerMatch': {"submissionID" : submissionID, "reviewerID": reviewerID}}
    r = requests.post(self.server_url + 'peermatch/create', data = json.dumps(params))
    #TODO: error checking
    return json.loads(r.text)

  def peermatch_get(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get', params)
    #TODO: error checking
    return r.json()['peerMatches']

  def peermatch_create_bulk(self, assignmentID, peerMatchesList):
    params = {'assignmentID': assignmentID, 'peerMatches': peerMatchesList}
    r = self.server_post('peermatch/create_bulk', params)
    if r.text:
      print r.text
      return json.loads(r.text)
    return r

  def peermatch_delete_all(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_post('peermatch/delete_all', params)
    if r.text:
        return json.loads(r.text)
    else:
        return r


  def peermatch_get_peer_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get_peer_ids', params)
    return r.json()['peerList']

  def peermatch_get_submission_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get_submission_ids',params)
    return r.json()['submissionList']

  def peermatch_get_peer_and_submission_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get_peer_and_submission_ids', params)
    return r.json()

  def peermatch_delete_match_bulk(self, match_id_list):
      params = {'matchIDList': match_id_list}
      r = self.server_post('peermatch/delete_match_bulk', params)
      if r.text:
        print r.text
        return json.loads(r.text)
      else:
        return r

  def set_review_grade(self, matchID, grade):
      params = {'matchID': matchID, 'grade': grade}
      r = self.server_post('peermatch/insert_review_mark', params)
      return r

  def set_review_grade_bulk(self, list_of_scores):
      params = {'reviewMarks': list_of_scores}
      r = self.server_post('peermatch/insert_review_marks_bulk', params)
      return r

  def peermatch_swap_review_match(self, match_ID, new_review_id):
      params = {'matchID': match_ID, 'reviewerToSwapID': new_review_id}
      r = self.server_post('peermatch/swap_peer_review', params)
      return r

  ############################### PEER REVIEWS ##############################

  def create_peerreview_int(self, match_id, question_id, answer_int):
      r = self.server_post('peerreviewscores/create_int', {'matchID': match_id, 'questionID': question_id, 'answerInt': answer_int})
      return r

  def create_peerreview_text(self, match_id, question_id, answer_text):
      r = self.server_post('peerreviewscores/create_text', {'matchID': match_id, 'questionID': question_id, 'answerText': answer_text})
      return r

  def create_peerreview(self, dict_params):
      '''{'match_id': matchid, 'question_id': questionid, 'answer_type': 'string'|'int','answer_value':val}'''
      if dict_params['answer_type'] == 'int':
          return self.create_peerreview_int(dict_params['match_id'], dict_params['question_id'], dict_params['answer_value'])
      elif dict_params['answer_type'] == 'string':
          return self.create_peerreview_text(dict_params['match_id'], dict_params['question_id'], dict_params['answer_value'])


  def create_peerreviews_bulk(self, listofparams):
      for d in listofparams:
          self.create_peerreview(d)

 

# GET_PEERREVIEWS
#    - returns {submission -> [review,...],...}
#    - review['answer'] is dictionary (if no answers, then empty dictionary)
#    - answers['int'] is an integer or None.
  def get_peerreviews(self, assignmentID, courseID = None):
    if courseID == None:
        courseID = self.courseID
    peerreview_params = locals()
    del peerreview_params['self']
    
    pr = self.server_get('peerreviewscores/get', peerreview_params).json()
    
    # replace [] with {} for 'answers' (seems to be a synonym in the JSON decoder)
    for item in [item for items in pr.values() for item in items]:
        if not item['answers']:
            item['answers'] = {}
            
    # make answer number 'int' an integer.
    for q, a in [qanda for items in pr.values() 
                       for item in items #if item['answers']
                       for qanda in item['answers'].items()]:
        if a['int']:
            a['int'] = int(a['int'])
    
    # make questionID an int.
    for item in [item for items in pr.values() for item in items]:
        item['answers'] = {int(q):a for q,a in item['answers'].items()}
    
    return pr
        
        
 
 
# GET_PEERREVIEW_SCORES
#    - returns {submission -> [reviews]}
#    - scores are added from rubric
#    - reviews with "no answer" are marked with NonScore.NO_ANSWER.
#    - reviews with option label "skip" are marked with NonScore.SKIP. 
  def get_peerreview_scores(self, assignmentID,courseID = None, rewrites = {}):
    if courseID == None:
        courseID = self.courseID
    
    pr = self.get_peerreviews(assignmentID, courseID)
    rubric = self.get_rubric(assignmentID)


    
    # add score to each question's answer
    for answers in [review['answers'] for reviews in pr.values() 
                       for review in reviews]:
        
        # add scores.
        for q,a in answers.items():
            # if rubric has options, then add score.
            if 'options' in rubric[q]:
              label = rubric[q]['options'][a['int']]['label'] 
              if label in rewrites:
                  a['score'] = rewrites[label]
              else:
                  a['score'] = rubric[q]['options'][a['int']]['score']
       
        # add q for unaswered questions if None is in rewrites
        if None in rewrites:
          for q in rubric.keys():
            if q not in answers:
              answers[q] = {'int': None, 'text': None}
              if 'options' in rubric[q]:
                answers[q]['score'] = rewrites[None]

    return pr


  ############################### TESTING ##############################

  def make_submissions(self, assignmentID, courseID = None):
    if courseID == None:
        courseID = self.courseID
    make_submissions_params = locals()
    del make_submissions_params['self']
    return requests.post(self.server_url + 'makesubmissions', data = json.dumps(make_submissions_params))


## WHAT IS THIS FOR?  --Jason

  def get_course_id_from_name(self, course_name):
    return requests.get(self.server_url + 'getcourseidfromname', data = json.dumps({'courseName' : course_name}))


  ################################ HELPERS ################################

# return the average of the numbers in the list.
  def avg(lst):
    return sum(lst)/len(lst) if len(lst) > 0 else 0.0

  def local_to_UTC(self, temp_datetime):
      return self.timezone.normalize(self.timezone.localize(temp_datetime)).astimezone(pytz.utc)

  def UTC_to_unix_timestamp(self, temp_datetime):
    return calendar.timegm(temp_datetime.utctimetuple())

  def string_time_to_datetime(self, string_time):
    return datetime.strptime(string_time, self.date_fmt)

  def convert_assignment_datetimes_to_unix_time(self, dict_to_update):
    time_fields = ['submissionStartDate', 'submissionStopDate', 'reviewStartDate', 'reviewStopDate', 'markPostDate', 'appealStopDate']
    for key in time_fields:
      if key in dict_to_update and type(dict_to_update[key]) is str:
        dict_to_update[key] = self.UTC_to_unix_timestamp(self.local_to_UTC(self.string_time_to_datetime(dict_to_update[key])))

  def add_day_offset(self, day_offset, dict_to_update):
    time_fields = ['submissionStartDate', 'submissionStopDate', 'reviewStartDate', 'reviewStopDate', 'markPostDate', 'appealStopDate']
    seconds_to_add = timedelta(days=day_offset).total_seconds()
    for key in time_fields:
      dict_to_update[key] += seconds_to_add


  ################################ EVENTS ################################
  def event_get(self, courseID, assignmentID=None):
      if assignmentID:
          params = {'courseID': courseID, 'assignmentID': assignmentID}
      else:
          params = {'courseID': courseID}
      r = requests.get(self.server_url + 'event/get', data=json.dumps(params))
      json_response = ''
      try:
          json_response = json.loads(r.text)
      except Exception:
          print r.text
          raise
      return json_response

  def event_create(self, assignmentID, summary, details, success,job):
      params = {'assignmentID': assignmentID,'summary': summary, 'details':
                details, 'success': success, 'job': job}
      r = requests.post(self.server_url + 'event/create',
                        data=json.dumps(params))
      return json.loads(r.text)

