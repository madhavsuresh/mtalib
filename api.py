import requests, json, string, copy, pprint, pytz, calendar, time
from datetime import datetime, timedelta
from pytz import timezone

class server_accessor:
  """Class for accessing the Mechanical TA API"""
  server_url = ''
  timezone = ''
  date_fmt = ''

  def __init__(self, p_server_url, local_timezone = 'US/Central', date_fmt = '%m/%d/%Y %H:%M:%S'):
    """Creates a server_accessor instance. Required param: p_server_url - MechTA instance API url. Optional params: local_timezone - pytz formatted timezone (default value: US/Central), date_fmt - string format for passed in dates (default value: '%m/%d/%Y %H:%M:%S')"""
    if p_server_url[-1:] != '/':
      p_server_url += '/'
    self.server_url = p_server_url;
    self.timezone = timezone(local_timezone)
    self.date_fmt = date_fmt

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

  def update_course(self, courseID, name='', displayName='', authType='', registrationType='', browsable=''):
    """Updates course specified by courseID with any additional optional parameters specified by user"""
    params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    del params['self']
    course_params = {key:value for (key, value) in params.iteritems() if value}

    return requests.post(self.server_url + 'course/update', data=json.dumps(course_params))

  def delete_course(self, courseID):
    """Deletes the course specified by ID"""
    delete_data = {'courseID' : courseID}
    return requests.post(self.server_url + 'course/delete', data=json.dumps(delete_data))

  def get_course(self, courseID=""):
    """If a courseID is supplied this returns the information associated with that class, without a specified courseID this returns a list of courses with courseID, name, displayName and browsable values for each course"""
    get_data = {}
    if courseID:
      get_data['courseID'] = courseID
    return requests.get(self.server_url + 'course/get', data=json.dumps(get_data))

  ############################ USERS ###########################

  def create_users(self, course_id, list_of_users):
    """Accepts a courseID and a list of user dictionaries and creates the given users under that course"""
    create_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/create', data = json.dumps(create_data))

  def update_users(self, course_id, list_of_users):
    """Accepts a courseID and a list of user dictionaries and updates the given users under that course"""
    update_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/update', data = json.dumps(update_data))

  def delete_users(self, course_id, list_of_users):
    """Accepts a courseID and a list of usernames and drops the given users under that course"""
    delete_data = {'courseID' : course_id, 'users' : list_of_users}
    return requests.post(self.server_url + 'user/delete', data = json.dumps(delete_data))

  def get_users(self, course_id, list_of_users=""):
    """Accepts a courseID and an optional list of usernames. Without the list of usernames this returns a list of users by username in the given course, with the optional list this returns more detailed info on each given username"""
    get_data = {'courseID' : course_id}
    if list_of_users:
      get_data['users'] = list_of_users
    return requests.get(self.server_url + 'user/get', data = json.dumps(get_data))

  ################################## Assignments ######################################

  def create_assignment(self, courseID, name, submissionQuestion, submissionStartDate = 1472352458, submissionStopDate = 2472352458, reviewStartDate = 1472352458, reviewStopDate = 2472352458, markPostDate = 2472352458, appealStopDate = 2472352458, day_offset = 0, maxSubmissionScore = 10, maxReviewScore = 5, defaultNumberOfReviews = 3, submissionType = 'essay'):
    """Creates an assignment based on the passed in parameters and on hardcoded defaults. Accepts either Unix epoch time or local time in format specified by constructor. Date parameters - [submissionStartDate, submissionStopDate, reviewStartDate, reviewStopDate, markPostDate, appealStopDate]. Also accepts a time offset in days."""
    assignment_params = locals()
    del assignment_params['self']

    defaults = {'password' : None, 'passwordMessage' : None, 'visibleToStudents' : 1, 'assignmentType' : 'peerreview', 'dateFormat' : 'MMMM Do YYYY, HH:mm', 'calibrationPoolAssignmentIds' : [], 'extraCalibrations' : 0, 'calibrationStartDate' : 0, 'calibrationStopDate' : 0, 'showMarksForReviewsReceived' : 1, 'showOtherReviewsByStudents' : 0, 'showOtherReviewsByInstructors' : 0, 'showMarksForOtherReviews' : 0, 'showMarksForReviewedSubmissions' : 0, 'showPoolStatus' : 0, 'calibrationMinCount' : 0, 'calibrationMaxScore' : 0, 'calibrationThresholdMSE' : 0, 'calibrationThresholdScore' : 0, 'allowRequestOfReviews' : 0, 'submissionSettings' : {'topics' : [], 'autoAssignEssayTopic' : 1, 'essayWordLimit' : 10000}}

    defaults.update(assignment_params)
    self.convert_assignment_datetimes_to_unix_time(defaults)
    if day_offset:
      self.add_day_offset(day_offset, defaults)
    return requests.post(self.server_url + 'assignment/create', data = json.dumps(defaults))

  def update_assignment(self, courseID, name, submissionQuestion, submissionStartDate = 1472352458, submissionStopDate = 2472352458, reviewStartDate = 1472352458, reviewStopDate = 2472352458, markPostDate = 2472352458, appealStopDate = 2472352458, day_offset = 0, maxSubmissionScore = 10, maxReviewScore = 5, defaultNumberOfReviews = 3, submissionType = 'essay'):
    """Updates an assignment based on the passed in parameters and on hardcoded defaults. Accepts either Unix epoch time or local time in format specified by constructor."""
    assignment_params = locals()
    del assignment_params['self']
    defaults = {'password' : None, 'passwordMessage' : None, 'visibleToStudents' : 1, 'assignmentType' : 'peerreview', 'dateFormat' : 'MMMM Do YYYY, HH:mm', 'calibrationPoolAssignmentIds' : [], 'extraCalibrations' : 0, 'calibrationStartDate' : 0, 'calibrationStopDate' : 0, 'showMarksForReviewsReceived' : 1, 'showOtherReviewsByStudents' : 0, 'showOtherReviewsByInstructors' : 0, 'showMarksForOtherReviews' : 0, 'showMarksForReviewedSubmissions' : 0, 'showPoolStatus' : 0, 'calibrationMinCount' : 0,'calibrationMaxScore' : 0,'calibrationThresholdMSE' : 0,'calibrationThresholdScore' : 0, 'allowRequestOfReviews' : 0, 'submissionSettings' : {'topics' : [], 'autoAssignEssayTopic' : 1, 'essayWordLimit' : 10000}}

    defaults.update(assignment_params)
    self.convert_assignment_datetimes_to_unix_time(defaults)
    if day_offset:
      self.add_day_offset(day_offset, defaults)
    return requests.post(self.server_url + 'assignment/update', data = json.dumps(assignment_params))

  def get_assignment(self, courseID, assignmentIDs):
    """Takes a courseID and a list of assignmentIDs and returns the information of the given assignments"""
    assignment_params = locals()
    del assignment_params['self']
    print assignment_params
    return requests.get(self.server_url + 'assignment/get', data = json.dumps(assignment_params))

  ################################## Rubrics ##########################################

  def create_rubric(self, courseID, assignmentID, name, question = 'test question?', hidden = 0, displayPriority = 0, options = [{'label' : 'A' , 'score' : 5.0}, {'label' : 'B' , 'score' : 4.0}, {'label' : 'C' , 'score' : 3.0}, {'label' : 'D' , 'score' : 2.0}, {'label' : 'E' , 'score' : 1.0}]):
    """Creates rubric for given courseID and assignmentID with given name"""
    rubric_params = locals()
    del rubric_params['self']

    return requests.post(self.server_url + 'rubric/create', data = json.dumps(rubric_params))

  def update_rubric(self, courseID, assignmentID, name, question = 'test question?', hidden = 0, displayPriority = 0, options = [{'label' : 'A' , 'score' : 5.0}, {'label' : 'B' , 'score' : 4.0}, {'label' : 'C' , 'score' : 3.0}, {'label' : 'D' , 'score' : 2.0}, {'label' : 'E' , 'score' : 1.0}]):
    """Creates rubric for given courseID and assignmentID with given name"""
    rubric_params = locals()
    del rubric_params['self']

    return requests.post(self.server_url + 'rubric/update', data = json.dumps(rubric_params))

  def get_rubric(self, assignmentID):
    '''Gets all rubrics right now based on AssignmentID '''
    assignment_params = locals()
    del assignment_params['self']
    return requests.get(self.server_url + 'rubric/get', data = json.dumps(assignment_params))

  ############################### GRADES ##############################

  def set_grades(courseID, assignmentID, grades):
    """Sets grades for a given assignmentID under the given course using the passed in list of (submissionID, grades) tuples"""
    grades_params = locals()
    del grades_params['self']
    r = requests.post(server_url + 'grades/create', data = json.dumps(grades_params))

  ############################### TESTING ##############################

  def make_submissions(self, courseID, assignmentID):
    make_submissions_params = locals()
    del make_submissions_params['self']

    return requests.post(self.server_url + 'makesubmissions', data = json.dumps(make_submissions_params))

  def make_peer_reviews(self):
    # take assignmentID, create peerreviewscores for all students
    pass

  def create_peerreviewscores(self, peerreviewscores_params):
    return requests.post(self.server_url + 'peerreviewscores/create', data = json.dumps(peerreviewscores_params))

  def get_peerreviewscores(self):
    pass

  def get_course_id_from_name(self, course_name):
    return requests.get(self.server_url + 'getcourseidfromname', data = json.dumps({'courseName' : course_name}))

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
