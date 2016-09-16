import requests, json, string, copy, pprint, pytz, calendar, time
from datetime import datetime, timedelta
from pytz import timezone

class server_accessor:
  """Class for accessing the Mechanical TA API"""
  server_url = ''
  timezone = ''
  date_fmt = ''
  courseID = None

  def __init__(self, p_server_url, course_id = 1, local_timezone = 'US/Central', date_fmt = '%m/%d/%Y %H:%M:%S'):
    """Creates a server_accessor instance. Required param: p_server_url - MechTA instance API url. Optional params: local_timezone - pytz formatted timezone (default value: US/Central), date_fmt - string format for passed in dates (default value: '%m/%d/%Y %H:%M:%S')"""
    if p_server_url[-1:] != '/':
      p_server_url += '/'
    self.server_url = p_server_url;
    self.timezone = timezone(local_timezone)
    self.date_fmt = date_fmt
    self.courseID = course_id

  def __str__(self):
    """Prints the url this instance is accessing"""
    return self.server_url

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

  def delete_users(self, list_of_users, course_id = None):
    """Accepts a courseID and a list of usernames and drops the given users under that course"""
    if course_id == None:
        course_id = self.courseID
    delete_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/delete', data = json.dumps(delete_data))

  def get_users(self, course_id = None, list_of_users=""):
    """Accepts a courseID and an optional list of usernames. Without the list of usernames this returns a list of users by username in the given course, with the optional list this returns more detailed info on each given username"""
    if course_id == None:
        course_id = self.courseID
    get_data = {'courseID' : course_id}
    if list_of_users:
      get_data['users'] = list_of_users
    return requests.get(self.server_url + 'user/get', data = json.dumps(get_data))

  def get_tas_from_course(self, courseID):
    params = {'courseID': courseID}
    r = requests.get(self.server_url + 'user/get_tas_from_courseid', data=json.dumps(params))
    return json.loads(r.text)

  ################################## Assignments ######################################

  def create_assignment(self, name, submissionQuestion, submissionStartDate = 1472352458, submissionStopDate = 2472352458, reviewStartDate = 1472352458, reviewStopDate = 2472352458, markPostDate = 2472352458, appealStopDate = 2472352458, courseID = None, day_offset = 0, maxSubmissionScore = 10, maxReviewScore = 5, defaultNumberOfReviews = 3, submissionType = 'essay'):
    """Creates an assignment based on the passed in parameters and on hardcoded defaults. Accepts either Unix epoch time or local time in format specified by constructor. Date parameters - [submissionStartDate, submissionStopDate, reviewStartDate, reviewStopDate, markPostDate, appealStopDate]. Also accepts a time offset in days."""
    if courseID == None:
        courseID = self.courseID
    assignment_params = locals()
    del assignment_params['self']

    defaults = {'password' : 'null', 'passwordMessage' : 'null', 'visibleToStudents' : 1, 'assignmentType' : 'peerreview', 'dateFormat' : 'MMMM Do YYYY, HH:mm', 'calibrationPoolAssignmentIds' : [], 'extraCalibrations' : 0, 'calibrationStartDate' : 0, 'calibrationStopDate' : 0, 'showMarksForReviewsReceived' : 1, 'showOtherReviewsByStudents' : 0, 'showOtherReviewsByInstructors' : 0, 'showMarksForOtherReviews' : 0, 'showMarksForReviewedSubmissions' : 0, 'showPoolStatus' : 0, 'calibrationMinCount' : 0, 'calibrationMaxScore' : 0, 'calibrationThresholdMSE' : 0, 'calibrationThresholdScore' : 0, 'allowRequestOfReviews' : 0, 'submissionSettings' : {'topics' : [], 'autoAssignEssayTopic' : 1, 'essayWordLimit' : 10000}}

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
    r = requests.get(self.server_url + 'assignment/courseID_from_assignmentID', data=json.dumps(params))
    return json.loads(r.text)
  ################################## Rubrics ##########################################

  def create_rubric(self, assignmentID, name, courseID = None, question = 'test question?', hidden = 0, displayPriority = 0, options = [{'label' : 'A' , 'score' : 5.0}, {'label' : 'B' , 'score' : 4.0}, {'label' : 'C' , 'score' : 3.0}, {'label' : 'D' , 'score' : 2.0}, {'label' : 'E' , 'score' : 1.0}, {'label' : 'Pass', 'score' : -1.0}]):
    """Creates rubric for given courseID and assignmentID with given name"""
    if courseID == None:
        courseID = self.courseID
    rubric_params = locals()
    del rubric_params['self']
    return requests.post(self.server_url + 'rubric/create', data = json.dumps(rubric_params))

  def update_rubric(self, assignmentID, name, courseID = None, question = 'test question?', hidden = 0, displayPriority = 0, options = [{'label' : 'A' , 'score' : 5.0}, {'label' : 'B' , 'score' : 4.0}, {'label' : 'C' , 'score' : 3.0}, {'label' : 'D' , 'score' : 2.0}, {'label' : 'E' , 'score' : 1.0}]):
    """Creates rubric for given courseID and assignmentID with given name"""
    if courseID == None:
        courseID = self.courseID
    rubric_params = locals()
    del rubric_params['self']

    return requests.post(self.server_url + 'rubric/update', data = json.dumps(rubric_params))

  def get_rubric(self, assignmentID):
    '''Gets all rubrics right now based on AssignmentID '''
    assignment_params = locals()
    del assignment_params['self']
    return requests.get(self.server_url + 'rubric/get', data = json.dumps(assignment_params))

  ############################### GRADES ##############################

  def set_grades(assignmentID, grades, courseID = None):
    """Sets grades for a given assignmentID under the given course using the passed in list of (submissionID, grades) tuples"""
    if courseID == None:
        courseID = self.courseID
    grades_params = locals()
    del grades_params['self']
    r = requests.post(server_url + 'grades/create', data = json.dumps(grades_params))

################################ PEERMATCH ################################
  def peermatch_create(self, assignmentID, submissionID, reviewerID):
    params = {'assignmentID': assignmentID, 'peerMatch': {"submissionID" : submissionID, "reviewerID": reviewerID}}
    r = requests.post(self.server_url + 'peermatch/create', data = json.dumps(params))
    #TODO: error checking
    return json.loads(r.text)

  def peermatch_get(self, assignmentID): 
    params = {'assignmentID': assignmentID}
    r = requests.post(self.server_url + 'peermatch/get', data=json.dumps(params))
    #TODO: error checking
    return json.loads(r.text)
 
  def peermatch_create_bulk(self, assignmentID, peerMatchesList):
    params = {'assignmentID': assignmentID, 'peerMatches': peerMatchesList} 
    r = requests.post(self.server_url + 'peermatch/create_bulk', data=json.dumps(params))
    if r.text:
      return json.loads(r.text)
  def peermatch_delete_all(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = requests.post(self.server_url + 'peermatch/delete_all', data=json.dumps(params))
    return json.loads(r.text)
  def peermatch_get_peer_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = requests.post(self.server_url + 'peermatch/get_peer_ids', data=json.dumps(params))
    return json.loads(r.text)
	
  def peermatch_get_submission_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = requests.post(self.server_url + 'peermatch/get_submission_ids', data=json.dumps(params))
    return json.loads(r.text)

  def peermatch_get_peer_and_submission_ids(self, assignmentID):
    params = {'assignmentID': assignmentID}
    r = requests.get(self.server_url + 'peermatch/get_peer_and_submission_ids', data=json.dumps(params))
    return json.loads(r.text)
  ############################### TESTING ##############################

  def make_submissions(self, assignmentID, courseID = None):
    if courseID == None:
        courseID = self.courseID
    make_submissions_params = locals()
    del make_submissions_params['self']
    return requests.post(self.server_url + 'makesubmissions', data = json.dumps(make_submissions_params))

  def create_peerreviews(self, peerreviews_params):
    return requests.post(self.server_url + 'peerreviews/create', data = json.dumps(peerreviews_params))

  def get_peerreviews(self, assignmentID, courseID = None):
    if courseID == None:
        courseID = self.courseID
    peer_review_scores_params = locals()
    del peer_review_scores_params['self']
    return requests.get(self.server_url + 'peerreviewscores/get', data = json.dumps(peer_review_scores_params))

  def get_peerreview_grades(self, assignmentID,courseID = None):
    if courseID == None:
        courseID = self.courseID
    pr = self.get_peerreviews(assignmentID, courseID).json()
    rubrics = self.get_rubric(assignmentID).json()
    for key, value in pr.iteritems():
        for x in range(len(value)):
            answers = value[x]['answers']
            for answers_key, answers_values in answers.iteritems():
                for y in range(len(rubrics)):
                    if rubrics[y]['questionID']['id'] == answers_key: # check for unicode if this works
                        score_index = int(answers_values['int'])
                        options = rubrics[y]['options']
                        answers_values['score'] = float(options[score_index]['score'])
                        # print pr[key][x][answers_key]

    return pr

  def setup_for_vancover(self, assignmentID, courseID = None):
    if courseID == None:
        courseID = self.courseID
    responses = self.get_peerreview_grades(assignmentID, courseID)
    reviews = {}
    truth = {}
    for key, value in responses.iteritems():
        truth[int(key.encode('ascii'))] = 2.5
        for x in range(len(value)): # list of answers
            curr_peer = {}
            reviewer_id = int(value[x]['reviewerID']['id'].encode('ascii'))
            answers = value[x]['answers'] # a dictionary or peer review responses
            count = 0
            for questionID, result in answers.iteritems():
                new_question_id = key.encode('ascii') + ':' + str(count)
                count += 1
                if reviewer_id in reviews:
                    reviews[reviewer_id][new_question_id] = result['score']
                else:
                    reviews[reviewer_id] = {}
                    reviews[reviewer_id][new_question_id] = result['score']

    return reviews, truth

  def average_score(self, answer_dict):
    count = 0
    score = 0
    for key, value in answer_dict.iteritems():
        count += 1
        score += value['score']
    return score/count


  def get_course_id_from_name(self, course_name):
    return requests.get(self.server_url + 'getcourseidfromname', data = json.dumps({'courseName' : course_name}))

  def calculate_grades(self):
    # self.get_peerreview_grades()
    # stuff
    # self.set_grades()
    pass

  ################################ HELPERS ################################

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
