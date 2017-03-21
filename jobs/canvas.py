import requests
import re
from ..algo.util import *
import appeals

ACCESS_TOKEN = "junk"
HEADERS = {"Authorization": "Bearer " + ACCESS_TOKEN}


##
## DATA
##

course = "43581"

#
# TODO: write the code to read this.
#
assignments = [{'canvas_essay_id': 279322,
  'canvas_review_id': 279323,
  'mechta_id': 2,
  'name': 'Computers and Computation (Monday)',
  'number': 1},
 {'canvas_essay_id': 279324,
  'canvas_review_id': 279325,
  'mechta_id': 1,
  'name': 'Computers and Computation (Wednesday)',
  'number': 2},
 {'canvas_essay_id': 279326,
  'canvas_review_id': 279327,
  'mechta_id': 3,
  'name': 'Algorithms and Tractability (Monday)',
  'number': 3},
 {'canvas_essay_id': 279328,
  'canvas_review_id': 279329,
  'mechta_id': 4,
  'name': 'Algorithms and Tractability (Wednesday)',
  'number': 4},
 {'canvas_essay_id': 279330,
  'canvas_review_id': 279331,
  'mechta_id': 5,
  'name': 'Programming Languages and Compilers (Monday)',
  'number': 5},
 {'canvas_essay_id': 279332,
  'canvas_review_id': 279333,
  'mechta_id': 6,
  'name': 'Programming Languages and Compilers (Wednesday)',
  'number': 6},
 {'canvas_essay_id': 279334,
  'canvas_review_id': 279335,
  'mechta_id': 7,
  'name': 'Systems and Networks (Monday)',
  'number': 7},
 {'canvas_essay_id': 279336,
  'canvas_review_id': 279337,
  'mechta_id': 8,
  'name': 'Systems and Networks (Wednesday)',
  'number': 8},
 {'canvas_essay_id': 279338,
  'canvas_review_id': 279339,
  'mechta_id': 9,
  'name': 'Cryptography and Security (Monday)',
  'number': 9},
 {'canvas_essay_id': 279340,
  'canvas_review_id': 279341,
  'mechta_id': 10,
  'name': 'Cryptography and Security (Wednesday)',
  'number': 10},
 {'canvas_essay_id': 279342,
  'canvas_review_id': 279343,
  'mechta_id': 11,
  'name': 'Artificial Intelligence and Machine Learning (Monday)',
  'number': 11},
 {'canvas_essay_id': 279344,
  'canvas_review_id': 279345,
  'mechta_id': 12,
  'name': 'Artificial Intelligence and Machine Learning (Wednesday)',
  'number': 12},
 {'canvas_essay_id': 279346,
  'canvas_review_id': 279347,
  'mechta_id': 13,
  'name': 'Human Computer Interaction (Monday)',
  'number': 13},
 {'canvas_essay_id': 279348,
  'canvas_review_id': 279349,
  'mechta_id': 14,
  'name': 'Human Computer Interaction (Wednesday)',
  'number': 14},
 {'canvas_essay_id': 279350,
  'canvas_review_id': 279351,
  'mechta_id': 15,
  'name': 'Graphics and Vision (Monday)',
  'number': 15},
 {'canvas_essay_id': 279352,
  'canvas_review_id': 279353,
  'mechta_id': 16,
  'name': 'Graphics and Vision (Wednesday)',
  'number': 16},
 {'canvas_essay_id': 279354,
  'canvas_review_id': 279355,
  'mechta_id': 17,
  'name': 'Human Computation (Monday)',
  'number': 17},
 {'canvas_essay_id': 279356,
  'canvas_review_id': 279357,
  'mechta_id': 18,
  'name': 'Human Computation (Wednesday)',
  'number': 18},
 {'canvas_essay_id': 279358,
  'canvas_review_id': 279359,
  'mechta_id': 19,
  'name': 'Robotics (Monday)',
  'number': 19},
 {'canvas_essay_id': 279360,
  'canvas_review_id': 279361,
  'mechta_id': 20,
  'name': 'Robotics (Wednesday)',
  'number': 20}]

def set_course(c):
    course = c

def set_access_token(token):
    global ACCESS_TOKEN
    global HEADERS
    ACCESS_TOKEN = token
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
    success = r.status_code == 200

    if not success:
        print "failed to set grade on submission " + str(hw_id) + " for student " + str(user_id) + " to " + str(grade)

    return success




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





def get_students(accessor,course=course):
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

def get_mechta_to_canvas_student_ids(accessor,course=course):
    return mechta_to_canvas_student_ids(get_students(accessor,course))

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

def canvas_get_assignment_groups(course=course):
    groups = get_paginated(print_uri("/api/v1/courses/:course_id/assignment_groups",
                               {'course_id': course}), HEADERS)
    return groups



def canvas_new_assignment(name,assignment_group_id,position=None,published=False,course=course):
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
    
    params = {'course_id':course}
    
    r = requests.post(print_uri("/api/v1/courses/:course_id/assignments",params),headers=HEADERS,json=data)
    return r.json()['id']

def canvas_upload_submission_zero_grades(accessor,assignmentID,assignments,mechta_to_canvas):

    submitters = accessor.peermatch_get_peer_ids(assignmentID)

    students = mechta_to_canvas.keys()
    
    non_submitters = list(set(students) - set(submitters))

    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]    
    # add essay grades grade
    for i in non_submitters:
        g = 5.0  # give non-submitters the no-appeal bonus.

        canvas_uid = mechta_to_canvas[i]

        print "setting essay grade on assignment " + str(assn['canvas_essay_id']) + " for student " + str(canvas_uid) + " to " + str(g)
        canvas_set_grade(assn['canvas_essay_id'],canvas_uid,g)   
  
    


def canvas_upload_submission_grades(accessor,assignmentID,assignments,mechta_to_canvas):

    subgrades = accessor.get_submission_grades(assignmentID)
    subgrades = [(d['studentID'],d['submissionID'],d['score']) for d in subgrades]

    submitters = [i for (i,_,_) in subgrades]
    students = mechta_to_canvas.keys()    
    non_submitters = list(set(students) - set(submitters))
    
    # add zero grade for non-submitters to subgrades
    subgrades += [(i,-1,0.0) for i in non_submitters]


    appealed_submissions = appeals.get_appeal_submissions(accessor,assignmentID)
    
    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]    
    # add essay grades grade
    for (i,j,g) in reversed(subgrades):
        
        if i in mechta_to_canvas:
            no_appeal_boost = 5.0 if j not in appealed_submissions else 0.0

            canvas_uid = mechta_to_canvas[i]
            print "setting essay grade on assignment " + str(assn['canvas_essay_id']) + " for student " + str(canvas_uid) + " to " + str(g) + " + " + str(no_appeal_boost) 
            canvas_set_grade(assn['canvas_essay_id'],canvas_uid,g+no_appeal_boost)   
        else:
            print "MechTA student " + str(i) + " is not in Canvas"


def canvas_upload_review_grades(accessor,assignmentID,assignments,mechta_to_canvas):

    revgrades = accessor.get_peerreview_grades(assignmentID)
    
    # grade is the maximum review score.
    revgrades = tuples_to_kkv([(d['reviewerID'],d['submissionID'],d['score']) for d in revgrades])
    revgrades = [(i,max(jtog.values())) for i,jtog in revgrades.items()]
    
    
    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]
    
    # add essay grades grade
    for (i,g) in revgrades:
        if i in mechta_to_canvas:
            canvas_uid = mechta_to_canvas[i]
            print "setting review grade on assignment " + str(assn['canvas_review_id']) + " for student " + str(canvas_uid) + " to " + str(g)
            canvas_set_grade(assn['canvas_review_id'],canvas_uid,g)   
        else:
            print "MechTA student " + str(i) + " is not in Canvas"


def canvas_upload_grades(accessor,assignmentID,assignments,mechta_to_canvas):
    canvas_upload_submission_grades(accessor,assignmentID,assignments,mechta_to_canvas)
    canvas_upload_review_grades(accessor,assignmentID,assignments,mechta_to_canvas)
    
