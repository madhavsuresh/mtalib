import requests, json, string

class server_accessor:
  """Class for accessing the Mechanical TA API"""
  server_url = ''

  def __init__(self, p_server_url):
    """Creates a server_accessor instance which will make call to the specified url"""
    if p_server_url[-1:] != '/':
      p_server_url += '/'
    self.server_url = p_server_url;

  def __str__(self):
    """Prints the url this instance is accessing"""
    return self.server_url

  def create_course(self, name, displayName, authType='pdo', registrationType='Open', browsable=True):
    """Creates a course with optional values. name and displayName are required parameters and name must be unique for call to not return error"""
    course_params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    course_params.pop('self', None)
    r = requests.post(self.server_url + 'course/create', data=json.dumps(course_params))
    return r

  def update_course(self, courseID, name='', displayName='', authType='', registrationType='', browsable=''):
    """Updates course specified by courseID with any additional optional parameters specified by user"""
    params = locals()
    # hacky and ugly, not particularly robust, look to change in future
    params.pop('self', None)
    course_params = {key:value for (key, value) in params.iteritems() if value}

    r = requests.post(self.server_url + 'course/update', data=json.dumps(course_params))
    return r

  def delete_course(self, courseID):
    """Deletes the course specified by ID"""
    delete_data = {'courseID' : courseID}
    r = requests.post(self.server_url + 'course/delete', data=json.dumps(delete_data))
    return r

  def get_course(self, courseID=""):
    """If a courseID is supplied this returns the information associated with that class, without a specified courseID this returns a list of courses with courseID, name, displayName and browsable values for each course"""
    get_data = {}
    if courseID:
      get_data['courseID'] = courseID
    r = requests.get(self.server_url + 'course/get', data=json.dumps(get_data))
    return r

################################## Assignments ###############################################3#

  def create_assignment(self, assignment_params):
    print self.server_url + 'create/assignment'
    r = requests.post(self.server_url + 'assignment/create', data = json.dumps(assignment_params))
    print r
    return r

  def update_assignment(self, assignment_params):
    print self.server_url + 'update/assignment'
    r = requests.post(self.server_url + 'assignment/update', data = json.dumps(assignment_params))
    return r

  def get_assignment(self, params):
    print self.server_url + 'get/assignment'
    r = requests.get(self.server_url + 'assignment/get', data = json.dumps(params))
    return r

##################################rubrics ##############################################

  def create_rubric(self, rubric_params):
    print self.server_url + 'rubric/create'
    r = requests.post(self.server_url + 'rubric/create', data = json.dumps(rubric_params))
    return r

  def get_rubric(self, assignment_params):
    '''Gets all rubrics right now based on AssignmentID '''
    #$print self.server_url + 'rubric/get'
    print "world"
    r = requests.get(self.server_url + 'rubric/get', data = json.dumps(assignment_params))
    print "hello"
    return r

  def update_rubric(self, assignment_params):
    print self.server_url + 'rubric/update'
    r = requests.post(self.server_url + 'rubric/update', data = json.dumps(assignment_params))
    return r

############################### TESTING ##############################

  def make_submissions(self, params):
    print self.server_url + "makesubmissions"
    r = requests.post(self.server_url + 'makesubmissions', data = json.dumps(params))
    return r

  def create_peerreviewscores(self, peerreviewscores_params):
    print self.server_url + "peerreviewscores/create"
    r = requests.post(self.server_url + "peerreviewscores/create", data = json.dumps(peerreviewscores_params))
    return r
