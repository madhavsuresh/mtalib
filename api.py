import requests, json, string

class server_accessor:

	server_url = ''

	def __init__(self, p_server_url):
		if p_server_url[-1:] != '/':
			p_server_url += '/'
		self.server_url = p_server_url;

	def __str__(self):
		return self.server_url

	def create_course(self, course_params):
		print self.server_url + 'create'
		r = requests.post(self.server_url + 'create', data=json.dumps(course_params))
		return r

	def update_course(self, course_params):
		r = requests.post(self.server_url + 'update', data=json.dumps(course_params))
		return r

	def delete_course(self, courseID):
		delete_data = {'courseID' : courseID}
		r = requests.post(self.server_url + 'delete', data=json.dumps(delete_data))
		return r

	def get_course(self, courseID):
		get_data = {'courseID' : courseID}
		r = requests.get(self.server_url + 'get', data=json.dumps(delete_data))
		return r

################################## Assignments ###############################################3#

        def create_assignment(self, assignment_params):
            print self.server_url + 'create/assignment'
            r = request.post(self.server_url + 'assignment/create', data = json.dumps(assignment_params))

        def update_assignment(self, assignment_params):
            print self.server_url + 'update/assignment'
            r = request.post(self.server_url + 'assignment/update', data = json.dumps(assignment_params))

        def get_assignment(self, params):
            print self.server_url + 'get/assignment'
            r = request.post(self.server_url + 'assignment/get', data = json.dumps(params))

  ##################################rubrics ##############################################

        def create_rubric(self, rubric_params):
            print self.server_url + 'rubric/create'
            r = request.post(self.server_url + 'rubric/create', data = json.dumps(rubric_params))

        def get_rubric(self, assignment_params):
            '''Gets all rubrics right now based on AssignmentID '''
            print self.server_url + 'rubric/get'
            r = request.post(self.server_url + 'rubric/get', data = json.dumps(assignment_params))

        def update_rubric(self, assignment_params):
            print self.server_url + 'rubric/update'
            r = request.post(self.server_url + 'rubric/update', data = json.dumps(assignment_params))

