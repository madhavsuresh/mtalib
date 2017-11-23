import requests, json, string, pprint, pytz, calendar, time
from datetime import datetime, timedelta
from pytz import timezone
from requests.auth import HTTPBasicAuth
from copy import copy, deepcopy
from pprint import pprint
#import config

import logging
logger = logging.getLogger()

import param as param


REPLACE_GRADE = 'replace'
INCREASE_GRADE = 'increase'

class server_accessor:
  """Class for accessing the Mechanical TA API"""
  server_url = ''
  timezone = ''
  date_fmt = ''
  courseID = None

  def __init__(self, p_server_url, courseID = 1, local_timezone = 'US/Central', date_fmt = '%m/%d/%Y %H:%M:%S', username='', password='',paramfile='mtaparam.pkl',confirm_post=False,check_courseID=False):
    """Creates a server_accessor instance. Required param: p_server_url - MechTA instance API url. Optional params: local_timezone - pytz formatted timezone (default value: US/Central), date_fmt - string format for passed in dates (default value: '%m/%d/%Y %H:%M:%S')"""
    if p_server_url[-1:] != '/':
      p_server_url += '/'
    self.server_url = p_server_url;
    self.timezone = timezone(local_timezone)
    self.date_fmt = date_fmt
    self.courseID = courseID
    self.username = username
    self.password = password
    self.paramfile = paramfile
    self.confirm_post = confirm_post
    self.check_courseID = check_courseID

    self._set('server_url',self.server_url)
    if self._get('server_url') != self.server_url:
      logger.warn("parameter file %s is not writable.",self.paramfile)

  def __str__(self):
    """Prints the url this instance is accessing"""
    return self.server_url

  def server_get(self, endpoint, params):
      r = requests.get(self.server_url + endpoint, data=json.dumps(params), 
              auth=(self.username, self.password))
      return r

  def server_post(self, endpoint, params):
      if self.confirm_post:
        print "CONFIRM POST: %s" % endpoint
        pprint(params)
        s = raw_input("Continue (y/n)?")
        if "n" in s:
          print "CANCELING"
          raise

      r = requests.post(self.server_url + endpoint, data=json.dumps(params), 
              auth=(self.username, self.password))
      return r

  def check_connection(self,courseID=None):
    if courseID == None:
      courseID = self.courseID
    # would be better to ping a specific endpoint to check the connection.
    try:
      r = self.server_get('user/get_tas_from_courseid', {'courseID':courseID})
    except:
      return False
    return r.status_code == requests.codes.ok



  def _defined(self,key):
    return param.defined(self.paramfile,(self.server_url,key))

  def _get(self,key):
    return param.get(self.paramfile,(self.server_url,key))

  def _set(self,key,value):
    param.set(self.paramfile,(self.server_url,key),value)

  def _update(self,key,f):
    param.update(self.paramfile,(self.server_url,key),f)

  def _delete(self,key):
    param.delete(self.paramfile,(self.server_url,key))

  def _params(self):
    return param.read(self.paramfile)


  def set_params(self,name,courseID=None,**params):
    if not courseID:
      courseID = self.courseID

    p = (courseID,name)

    self._set(p,params)

  def update_params(self,name,courseID=None,**params):
    if not courseID:
      courseID = self.courseID

    p = (courseID,name)

    def add_params(x):
      if x:
        x.update(params)
        return x
      else:
        return params
    
    self._update(p, add_params)

  def get_params(self,name,courseID=None):
    if not courseID:
      courseID = self.courseID

    p = (courseID,name)
    
    if self._defined(p):
      return self._get(p)

    return {}

  def set_course_params(self,courseID=None,**params):
    self.set_params('course_params',courseID=courseID,**params)

  def update_course_params(self,courseID=None,**params):
    self.update_params('course_params',courseID=courseID,**params)
    
  def get_course_params(self,courseID=None):
    return self.get_params('course_params',courseID=courseID)

  def set_default_assignment_params(self,courseID=None,**params):
    self.set_params('default_assignment_params',courseID=courseID,**params)

  def update_default_assignment_params(self,courseID=None,**params):
    self.update_params('default_assignment_params',courseID=courseID,**params)
    
  def get_default_assignment_params(self,courseID=None):
    return self.get_params('default_assignment_params',courseID=courseID)


  def set_assignment_params(self,assignmentID,courseID=None,**params):
    self.set_params((assignmentID,'assignment_params'),courseID=courseID,**params)

  def update_assignment_params(self,assignmentID,courseID=None,**params):
    self.update_params((assignmentID,'assignment_params'),courseID=courseID,**params)
    
  def get_assignment_params_without_defaults(self,assignmentID,courseID=None):
    return self.get_params((assignmentID,'assignment_params'),courseID=courseID)

  def get_assignment_params(self,assignmentID,courseID=None):
    d_params = self.get_default_assignment_params(courseID=courseID)
    a_params = self.get_assignment_params_without_defaults(assignmentID,courseID=courseID)

    d_params.update(a_params)

    return d_params





  ############################ COURSE ###########################

  def create_course(self, name, displayName, authType='pdo',
                    registrationType='Open', browsable=True, gracePeriod=15):
    """Creates a course with optional values. name and displayName are required parameters and name must be unique for call to not return error"""
    course_params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    del course_params['self']
    return requests.post(self.server_url + 'course/create', data=json.dumps(course_params))

  def update_course(self, courseID = None, name='', displayName='',
                    authType='', registrationType='', browsable='',
                    gracePeriod=None):
    """Updates course specified by courseID with any additional optional parameters specified by user"""
    """Grace period is in minutes"""
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

  def get_course(self, courseID=None):
    """If a courseID is supplied this returns the information associated with that class, without a specified courseID this returns a list of courses with courseID, name, displayName and browsable values for each course"""
    get_data = {}
    if courseID:
      get_data['courseID'] = courseID
    x = self.server_get('course/get', get_data)
    return x.json()



  ############################ Users ###########################

  def create_users(self, list_of_users, courseID = None):
    """Accepts a courseID and a list of user dictionaries and creates the given users under that course"""
    if courseID == None:
        courseID = self.courseID
    create_data = {'courseID' : courseID, 'users' : list_of_users}
    return self.server_post('user/create', create_data)

  def update_users(self, users, courseID = None):
    """Accepts a courseID and a list of user dictionaries and updates the given users under that course"""
    if courseID == None:
        courseID = self.courseID
    update_data = {'courseID' : courseID, 'users' : users}
    return self.server_post('user/update', update_data)

  def delete_users(self, users, courseID = None):
    if courseID == None:
        courseID = self.courseID

    if not users:
      return True

    logger.info('deleting users %s',str(users))

    # save dropped users in param.
    self._update((courseID,'dropped_users'),lambda x : list(set(x + users)) if x else users)
    all_users = self.get_all_users(courseID=courseID)
    usernames = [u['username'] for u in all_users if u['userID'] in users]

    logger.info('deleting usernames %s',str(usernames))

    return self.delete_users_by_username(users=usernames,courseID=courseID)


  def delete_users_by_username(self, users, courseID = None):
    """Accepts a courseID and a list of usernames and drops the given users under that course"""
    if courseID == None:
        courseID = self.courseID
    delete_data = {'courseID' : courseID, 'users' : users}
    return self.server_post('user/delete', delete_data)

  # gets all student IDs, even dropped students.
  def get_all_students(self, courseID=None):
    users = self.get_all_users(courseID=courseID)
    student_ids = [u['userID'] for u in users if u['userType'] == 'student']
    return student_ids

  # gets student IDs from students who have not dropped.
  def get_students(self, courseID=None):
    if courseID == None:
        courseID = self.courseID

    students = self.get_all_students(courseID=courseID)

    dropped = self._get((courseID,'dropped_users'))

    if dropped:
      logger.info('get_students: withholding dropped students %s',str(dropped))
      students = list(set(students) - set(dropped))

    return students

  def get_dropped_students(self, courseID=None):
    if courseID == None:
        courseID = self.courseID

    
    dropped = self._get((courseID,'dropped_users'))
    
    return dropped if dropped else []

  def get_users(self, courseID = None, users=None):
    """Accepts a courseID and an optional list of usernames. Without the list of usernames this returns a list of users by username in the given course, with the optional list this returns more detailed info on each given username"""
    if courseID == None:
        courseID = self.courseID
    data = locals()
    del data['self']
    if not users:
      del data['users']
    r = self.server_get('user/get',data)


    if not users: # return a list of all userIDs.
      return [int(s['id']) for s in r.json()] 
    else:         # return list of dicts for each userID listed in 'users'
      dicts = r.json()

      # remove nested 'id' and convert to int.
      for s in dicts:
        for key in s.keys():
          if 'ID' in key:
            if not s[key]:
              logger.warn('user has invalid id for %s (details %s)',key,str(s))
            if s[key]:
              s[key] = int(s[key]['id']) if 'id' in s[key] else int(s[key])

      return dicts

  def get_all_users(self,courseID=None):
    return self.get_users(courseID,users=self.get_users(courseID))

  def get_graders(self,courseID=None):
    if courseID == None:
        courseID = self.courseID
    return self.get_tas(courseID=courseID,markingLoad=1)


  def get_tas(self, courseID=None, markingLoad=-1):
    if courseID == None:
        courseID = self.courseID
    params = {'courseID': courseID, 'markingLoad': markingLoad}
    r = self.server_get('user/get_tas_from_courseid', params)
    return r.json()['taIDs']

  # depricated.
  get_tas_from_course = get_tas
    
    

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

  # set full=True to get full record.
  def get_assignment_by_name(self,name,courseID=None,full=False):
    if courseID == None:
        courseID = self.courseID

    def return_value(record):
      return record if full else record['assignmentID']

    assignments = self.get_assignment(courseID=courseID)

    matching_assignments = [a for a in assignments if name in a['name']]
    
    if not matching_assignments:
      return None
    if len(matching_assignments) == 1:
      return return_value(matching_assignments[0])

    logger.warn('Multiple matching assignment names: %s',str([a['name'] for a in matching_assignments]))

    return matching_assignments

  def get_assignment(self, assignmentIDs = None, courseID = None):
    """Takes a courseID and a list of assignmentIDs and returns the information of the given assignments"""
    if courseID == None:
        courseID = self.courseID
    if not assignmentIDs:
      assignmentIDs='all'

    assignment_params = locals()
    del assignment_params['self']
    r = self.server_get('assignment/get', assignment_params)
    assignments = r.json()
    for a in assignments:
      a['assignmentID'] = int(a['assignmentID']['id'])
    return assignments

  def get_assignments(self,courseID=None):
    if courseID == None:
        courseID = self.courseID

    assignments = self.get_assignment(courseID=courseID)
    
    return [a['assignmentID'] for a in assignments]


  def get_courseID(self,assignmentID,courseID=None):
    if self.check_courseID or not courseID:
      confirmed_courseID = self.get_courseID_from_assignmentID(assignmentID)
    else:
      confirmed_courseID = courseID
    
    if not courseID:
      logger.warn("CourseID Check: No courseID set")
    elif courseID != confirmed_courseID:
      logger.warn("CourseID Check: CourseID mismatch.  Got %d, expected %d.",courseID,confirmed_courseID)

    return confirmed_courseID


  def get_courseID_from_assignmentID(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = self.server_get('assignment/courseID_from_assignmentID', params)

    courseID = r.json()['courseID']

    # will be None if there is no such assignment
    if courseID:
      courseID = int(courseID)

    return courseID


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

    params = deepcopy(defaults)
    params.update(kwargs)
    params['assignmentID'] = assignmentID
    params['courseID'] = courseID


    weight = params['weight']
    del params['weight']

    # scores can be normalized, and then reweighted by weight.
    # need to store reweighted scored in MTA.
    options = params['options']
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
  def get_rubric(self, assignmentID,courseID=None):
    '''Gets all rubrics right now based on AssignmentID '''
    assignment_params = locals()
    del assignment_params['self']
    
    req = self.server_get('rubric/get', assignment_params)
    questions = req.json()
    
    # make questionIDs ints
    # THIS SHUOLD HAPPEN IN THE API ENDPOINT BUT DOES NOT.
    for q in questions:
      q['questionID'] = int(q['questionID']['id'])
     
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
    
    rubric = {q['questionID']:q for q in questions}
    
    return rubric

  def get_rubric_weights(self,assignmentID):
    '''Gets rubric weights into dictionary {q:weight,...}'''
    rubric = self.get_rubric(assignmentID)

    # question weights: {q:weight,...}
    weights = {q:props['weight'] for q,props in rubric.items() if 'weight' in props}
 
    return weights


  ############################### APPEALS ##############################

  def get_all_appeals(self):
      # courseID is ignored.
      r = self.server_get('appeals/get', None);

      if not r.ok:
        logger.warn("error getting appeals from server")
        logger.warn("%s",r.text)
        return []

      return r.json()['appeals']

  def get_appeals(self,assignmentID=None,courseID=None):

    # backwards compatability, better not to use this.
    if not assignmentID:
      logger.warn("depricated usage of get_appeals without assignmentID, use get_all_appeals instead") 
      return self.get_all_appeals()

    appeals = self.get_all_appeals()

    courseID = self.get_courseID(assignmentID,courseID=courseID)

    matches_for_assignment = self.peermatch_get(assignmentID,courseID=courseID)
    subs = {m['matchID']:m['submissionID'] for m in matches_for_assignment}
    
    return [a for a in appeals if a['matchID'] in subs]


  def get_appeal_submissions(self,assignmentID,courseID=None):
    courseID = self.get_courseID(assignmentID,courseID=courseID)


    appeals = self.get_all_appeals()
    matches_for_assignment = self.peermatch_get(assignmentID,courseID=courseID)
    subs = {m['matchID']:m['submissionID'] for m in matches_for_assignment}
    
    return list(set([subs[a['matchID']] for a in appeals if a['matchID'] in subs]))


  def get_review_appeals_by_assignment(self, assignmentID,courseID=None):
      # courseID is ignored
      appeals = self.get_appeals_by_assignment(assignmentID)
      review_appeals = filter(lambda x: x['appealType'] == 'review', appeals)
      return review_appeals

  def get_reviewmark_appeals_by_assignment(self, assignmentID):
      appeals = self.get_appeals_by_assignment(assignmentID)
      reviewmark_appeals = filter(lambda x: x['appealType'] == 'reviewmark', appeals)
      return reviewmark_appeals

  def get_appeals_by_assignment(self, assignmentID):
      all_appeals = self.get_appeals()
      matches_for_assignment = self.peermatch_get(assignmentID)
      matchIDs = [match['matchID'] for match in matches_for_assignment] 
      appeals_for_assignment = filter(lambda x: x['matchID'] in matchIDs, all_appeals)
      return appeals_for_assignment
  
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

  # gets current submission grades, 
  # NOTE: if grade is missing, it fills in with zero.  
  #        (perhaps this should be changed)
  def get_submission_grades(self,assignmentID,courseID=None):

    jtog = {d['submissionID']:d['score'] for d in self.get_all_submission_grades()}

    subs = self.get_student_and_submission_ids(assignmentID)
    
    grades = [{'submissionID':j,
               'studentID':i,
               'grade':jtog[j] if j in jtog else 0.0}
              for (i,j) in subs]

    return grades
    

  def set_submission_grades(self,assignmentID, grades,mode=REPLACE_GRADE,courseID=None):
    """Sets grades for a given assignmentID under the given course using the passed in list [{'submissionID':...,'grade':...}...] """


    new_grades = {g['submissionID']:g['grade'] for g in grades}

    # find grades that are already set. 
    current_grades = {g['submissionID']:g['grade'] for g 
                      in self.get_submission_grades(assignmentID) 
                      if g['submissionID'] in new_grades.keys()}

    if mode == INCREASE_GRADE:
      update_grade = lambda new,old: max(new,old)
    else: # mode == REPLACE_GRADE
      update_grade = lambda new,old: new

    added_grades = [{'submissionID':m,'grade':g} 
                  for (m,g) in new_grades.items() 
                  if m not in current_grades]
    updated_grades = [{'submissionID':m,
                      'grade':update_grade(g,current_grades[m])} 
                     for (m,g) in new_grades.items() 
                     if m in current_grades] 


    return self.set_grades(assignmentID,[(g['submissionID'],g['grade']) for g in added_grades + updated_grades],courseID=courseID)


  def set_review_grade(self, matchID, grade,courseID=None):
      params = {'matchID': matchID, 'grade': grade}
      r = self.server_post('peermatch/insert_review_mark', params)
      return r

  # list_of_scores = [{'matchID':...,'grade':...},...]
  def set_review_grade_bulk(self, grades,courseID=None):
      params = {'reviewMarks': grades}
      r = self.server_post('peermatch/insert_review_marks_bulk', params)
      return r

  # 
  def set_review_grades(self,assignmentID,grades,mode=REPLACE_GRADE,courseID=None):

    new_grades = {g['matchID']:g['grade'] for g in grades}

    # find grades that are already set. 
    current_grades = {g['matchID']:g['grade'] for g 
                      in self.get_peerreview_grades(assignmentID) 
                      if g['matchID'] in new_grades.keys()}

    if mode == INCREASE_GRADE:
      update_grade = lambda new,old: max(new,old)
    else: # mode == REPLACE_GRADE
      update_grade = lambda new,old: new

    added_grades = [{'matchID':m,'grade':g} 
                  for (m,g) in new_grades.items() 
                  if m not in current_grades]
    updated_grades = [{'matchID':m,
                      'grade':update_grade(g,current_grades[m])} 
                     for (m,g) in new_grades.items() 
                     if m in current_grades] 


    return self.set_review_grade_bulk(added_grades + updated_grades)
      

  def get_peerreview_grades(self,assignmentID,courseID=None):

    courseID = self.get_courseID(assignmentID,courseID=courseID)

    grades = self.get_all_peerreview_grades()

    # [{'peerID':peerID,'submissionID':submissionID,'matchID':matchID} ...]
    peermatchs = self.peermatch_get(assignmentID)

    id_to_match = {d['matchID']:d for d in peermatchs}

    # filter for assignmentID, add peerID and submissionID
    grades = [dict(d,**id_to_match[d['matchID']]) for d in grades if d['matchID'] in id_to_match]


    # rename 'score' to 'grade'
    for d in grades:
      d['grade'] = d['score']
      del d['score']


    return grades

    

  def get_all_submission_grades(self):
     r = self.server_get('grades/submissions', None);
     return r.json()['scores']

  def get_all_peerreview_grades(self):
     r = self.server_get('grades/peerreviews', None);
     return r.json()['scores']

################################ PEERMATCH ################################
  def peermatch_create(self, assignmentID, submissionID, reviewerID,courseID=None):
    params = {'assignmentID': assignmentID, 'peerMatch': {"submissionID" : submissionID, "reviewerID": reviewerID}}
    r = requests.post(self.server_url + 'peermatch/create', data = json.dumps(params))
    #TODO: error checking
    return json.loads(r.text)

  def peermatch_get(self, assignmentID,courseID=None):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get', params)
    #TODO: error checking
    return r.json()['peerMatches']

  def peermatch_create_bulk(self, assignmentID, peerMatchesList,courseID=None):
    params = {'assignmentID': assignmentID, 'peerMatches': peerMatchesList}
    r = self.server_post('peermatch/create_bulk', params)
    if r.text:
      print r.text
      return json.loads(r.text)
    return r

  def peermatch_delete_all(self, assignmentID,courseID=None):
    params = {'assignmentID': assignmentID}
    r = self.server_post('peermatch/delete_all', params)
    if r.text:
        return json.loads(r.text)
    else:
        return r

  def peermatch_get_peer_ids(self, assignmentID,courseID=None):
    students = self.get_student_and_submission_ids(assignmentID)
    return [i for (i,_) in students]

  def peermatch_get_submission_ids(self, assignmentID,courseID=None):
    students = self.get_submitter_and_submission_ids(assignmentID)
    return [j for (_,j) in students]

  def get_submitter_and_submission_ids(self, assignmentID,courseID=None):
    data = self.peermatch_get_peer_and_submission_ids(assignmentID)['peerSubmissionPairs']
    return [(d['peerID'],d['submissionID']) for d in data]

  def get_student_and_submission_ids(self, assignmentID,courseID=None):
    submitters = self.get_submitter_and_submission_ids(assignmentID)
    partners = self.get_partner_and_submission_ids(assignmentID)

    return submitters+partners


  # BADLY NAMED!  Gets *student* and submission)
  # use wrapper above instead!!
  def peermatch_get_peer_and_submission_ids(self, assignmentID,courseID=None):
    params = {'assignmentID': assignmentID}
    r = self.server_get('peermatch/get_peer_and_submission_ids', params)
    return r.json()

  def peermatch_delete_match_bulk(self, match_id_list,courseID=None):
      params = {'matchIDList': match_id_list}
      r = self.server_post('peermatch/delete_match_bulk', params)
      if r.text:
        print r.text
        return json.loads(r.text)
      else:
        return r


  def peermatch_swap_review_match(self, match_ID, new_review_id,courseID=None):
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
    

    if not pr:
      return {}

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

    # fix ids to be integers, and remove nested structure.
    pr = {int(i):reviews for i,reviews in pr.items()}
    for reviews in pr.values(): 
      for review in reviews:
        for key in review.keys():
          if 'ID' in key:
            review[key] = int(review[key]['id'])

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
  def event_get(self, courseID=None, assignmentID=None):
      if courseID == None:
        courseID = self.courseID
      params = locals()
      del params['self']
      if not assignmentID:
         del params['assignmentID']
      r = self.server_get('event/get', params)
      json_response = ''
      try:
          json_response = json.loads(r.text)
      except Exception:
          print r.text
          raise
      return json_response['eventList']

  def event_create(self, assignmentID, job, success, summary, details,courseID=None):
      if courseID is None:
        courseID = self.courseID
      params = locals()
      del params['self']
      r = self.server_post('event/create',params)
      return r


  ################################ PARTNER ################################
  def partner_get(self, assignmentID):
      params = {'assignmentID': assignmentID}
      r = self.server_get('partner/get', params)
      return r.json()

  def partner_get_unpacked(self, assignmentID):
     partners = self.partner_get(assignmentID)
     return_list = []
     for p in partners['partnerPairAndSubmissionList']:
         return_list.append({'submissionID': p['submissionID'],
                             'peers':[p['peerOwnerID'], p['peerPartnerID']]})
     return return_list

  def get_partner_and_submission_ids(self,assignmentID):
     partners = self.partner_get(assignmentID=assignmentID)['partnerPairAndSubmissionList']
     return [(d['peerPartnerID'],d['submissionID']) for d in partners]
    
