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
