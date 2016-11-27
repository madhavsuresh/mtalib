course = "43581"
ACCESS_TOKEN = "1876~6qGWmwdADNBAUiMr4vJ0mmxi0pBh31cx9XQii96WI2XbG7hYbnBKWcxmOdR8tukJ"
HEADERS = {"Authorization": "Bearer " + ACCESS_TOKEN}




##
## BASIC CANVAS API ACCESS
##

def get_json(uri,headers):
    r = requests.get(uri,headers=headers)
    data_set = []  
    raw = r.json()   
    return raw



def get_paginated(uri,headers=None,params=None):

    r = requests.get(uri,headers=headers,params=params)

    data_set = []  

    raw = r.json()

    for question in raw:  
        data_set.append(question)  

    if 'current' in r.links:
        while r.links['current']['url'] != r.links['last']['url']:  
            r = requests.get(r.links['next']['url'], headers=headers)  
            raw = r.json()  
            for question in raw:  
                data_set.append(question)  

    return data_set


def print_uri(uri,params):
    dict_replace = lambda word: str(params[word]) if (word in params) else ":" + word
    match_func = lambda m: dict_replace(m.group(1))

    return "https://canvas.northwestern.edu" + re.sub(":(\w+)",match_func,uri)

##
## SET GRADE ON CANVAS
##
def canvas_set_grade(hw_id,user_id,grade):
    r = requests.put(print_uri("/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id",
                               {'course_id': course, 'assignment_id': hw_id, 'user_id': user_id}),
                     headers=HEADERS,params={'submission[posted_grade]':grade})
    return




##
## GET STUDENT FROM CANVAS 
## MAP MechTA STUDENT TO CANVAS STUDENTS
##


#Amber I: Thank you for your patience while I looked into this for you. 
#    After speaking with our L2, we recommend that you use this API call 
#    instead as the other one is depreciated and this call will provide 
#    the most accurate information: 
#        /api/v1/courses/:courseid:/users?enrollment_type=student&per_page=100&page=1 
#    You can find information on this call being depreciated here: 
#        https://canvas.instructure.com/doc/api/all_resources.html#method.courses.students





def get_students(course=course,accessor=accessor):
    students = canvas_get_students(course)
    
    net_ids = [s['net_id'] for s in students]
    
    mechta_users = accessor.get_users(courseID=1,users=net_ids)

    mechta_ids = {u['username']:int(u['userID']['id']) for u in mechta_users}
    
    for s in students:
        if s['net_id'] in mechta_ids:
            s['mechta_id'] = mechta_ids[s['net_id']]
        else:
            print str(s['net_id']) + " is not enrolled in MechTA."
    
    students = [s for s in students if 'mechta_id' in s]
    
    return students


def mechta_to_canvas_student_ids(students):
    mechta_to_canvas = {s['mechta_id']:s['canvas_id'] for s in students}
    return mechta_to_canvas

def get_mechta_to_canvas_student_ids(course=course):
    return mechta_to_canvas_student_ids(get_students(course))

def canvas_get_studentIDs(course=course):
    students = get_paginated(print_uri("/api/v1/courses/:course_id/students",
                            {'course_id': course}), HEADERS)

    studentIDs = [s['sis_login_id'] for s in students]

    return studentIDs

def canvas_get_students(course=course):
    students = get_paginated(print_uri("/api/v1/courses/:course_id/students",
                               {'course_id': course}), HEADERS)

    print (len(students))
    
    students = [{'net_id':s['login_id'],'canvas_id':s['id']} for s in students]

    return students

##
## CREATE & LIST ASSIGNMENTS and ASSIGNMENT GROUPS on CANVAS
##

def canvas_get_assignment_groups(course=canvas_course):
    groups = get_paginated(print_uri("/api/v1/courses/:course_id/assignment_groups",
                               {'course_id': course}), HEADERS)
    return groups



def canvas_new_assignment(name,assignment_group_id,position=None,published=False,course=canvas_course):
    data = {'assignment':{
            'name':name,
            'assignment_group_id':assignment_group_id,
            'points_possible':100,
            'grading_type':'percent',
            'published':published,
            'submission_types':['none']
        }}
    if position:
        data['assignment']['position'] = position
    
    params = {'course_id':canvas_course}
    
    r = requests.post(print_uri("/api/v1/courses/:course_id/assignments",params),headers=HEADERS,json=data)
    return r.json()['id']




def canvas_upload_grades(accessor,assignmentID,assignments,mechta_to_canvas,accessor=accessor):
    
    # recalculate grades (since we cannot get them from mechta, no API for it)
    revgrades = accessor.get_peerreview_grades(assignmentID)
    
    # grade is the maximum review score.
    revgrades = tuples_to_kkv([(d['reviewerID'],d['submissionID'],d['score']) for d in revgrades])
    revgrades = [(i,max(jtog.values())) for i,jtog in revgrades.items()]
    
    subgrades = accessor.get_submission_grades(assignmentID)
    
    subgrades = [(d['studentID'],d['score']) for d in subgrades]

    
    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]
    
    # add essay grades grade
    for (i,g) in subgrades:
        if i in mechta_to_canvas:
            canvas_uid = mechta_to_canvas[i]
            print "setting essay grade on assignment " + str(assn['canvas_essay_id']) + " for student " + str(canvas_uid) + " to " + str(g)
            canvas_set_grade(assn['canvas_essay_id'],canvas_uid,g)   
        else:
            print "MechTA student " + str(i) + " is not in Canvas"

    # add essay grades grade
    for (i,g) in revgrades:
        if i in mechta_to_canvas:
            canvas_uid = mechta_to_canvas[i]
            print "setting review grade on assignment " + str(assn['canvas_review_id']) + " for student " + str(canvas_uid) + " to " + str(g)
            canvas_set_grade(assn['canvas_review_id'],canvas_uid,g)   
        else:
            print "MechTA student " + str(i) + " is not in Canvas"
