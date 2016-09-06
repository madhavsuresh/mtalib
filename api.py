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
		print self.server_url + 'course/create'
		r = requests.post(self.server_url + 'course/create', data=json.dumps(course_params))
		return r

	def update_course(self, course_params):
		r = requests.post(self.server_url + 'course/update', data=json.dumps(course_params))
		return r

	def delete_course(self, courseID):
		delete_data = {'courseID' : courseID}
		r = requests.post(self.server_url + 'course/delete', data=json.dumps(delete_data))
		return r

	def get_course(self, courseID):
		get_data = {'courseID' : courseID}
		r = requests.get(self.server_url + 'course/get', data=json.dumps(delete_data))
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

