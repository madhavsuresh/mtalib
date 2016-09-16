import random
from python_lib.api import *
c = server_accessor('http://enron.cs.northwestern.edu/~nathan/mta/api/')
randomUniqueCourseName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
print randomUniqueCourseName
course_create_data = {'name' : randomUniqueCourseName, 'displayName' : 'test', 'authType' : 'pdo', 'registrationType' : 'Open', 'browsable' : True}
r = c.create_course(course_create_data)
print r, r.text
