import requests
import re
from ..algo.util import *


import logging

logger = logging.getLogger()


ACCESS_TOKEN = "junk"
HEADERS = {"Authorization": "Bearer " + ACCESS_TOKEN}


##
## DATA
##

course = "59877"



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
## ASSIGNMENTS
##
def canvas_get_assignments(course):
    assignments = get_paginated(print_uri("/api/v1/courses/:course_id/assignments",
                            {'course_id': course}), HEADERS)

    if 'errors' in assignments:
        logger.warn("error retrieving assignments from canvas")
        assignments = []

    return assignments


def get_canvas_course_from_accessor(accessor,courseID=None):
    if not courseID:
        courseID=accessor.courseID

    c_params = accessor.get_course_params(courseID=courseID)
    if not 'canvas_course' in c_params:
        logger.warn('canvas_course parameter not configured for courseID %d',courseID)
        return None
    
    return c_params['canvas_course']


##
# reads from MechTA and Canvas 
# matches MechTA assignments with Canvas assignments
# returns:
#   [{'name':...,
#     'mechta_id':...,
#     'canvas_submission_id':...,
#     'canvas_review_id':...},
#     ...]
def get_assignments(accessor,courseID=None,submission_name="Problem",review_name="Peer Review"):

    if not courseID:
        courseID = accessor.courseID

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn('canvas_course parameter not configured for courseID %d',courseID)
        return []

    canvas_assignments=canvas_get_assignments(course)
    
    mechta_assignments=accessor.get_assignment(courseID=courseID)

    def strip_to_number(name):
        m = re.search('(\d+(\.\d+)?)', name)
        if m:
            found = m.group(1)
            return found
        else:
            return name

    def get_canvas_assignment_id(number,also_match):
        ids = [a['id'] for a in canvas_assignments if number == strip_to_number(a['name']) and also_match in a['name']]

        if len(ids) > 1:
            logger.warn("too many canvas assignments match %s: %s",number,str(ids))

        if ids:
            return ids[0]
        else:
            logger.warn("no canvas assignments match %s (%s)",number,also_match)
            return None

    idandnames = [(a['assignmentID'],a['name'],a['maxSubmissionScore'],a['maxReviewScore']) for a in mechta_assignments]

    assignments = [{'mechta_id':id,
                    'submission_points': submission_points,
                    'review_points':review_points,
                    'name':name,
                    'canvas_submission_id':get_canvas_assignment_id(strip_to_number(name),submission_name),
                    'canvas_review_id':get_canvas_assignment_id(strip_to_number(name),review_name)}
                   for (id,name,submission_points,review_points) in idandnames]
        
    return assignments
                    

##
## SET GRADE ON CANVAS
##
def canvas_set_grade(course, hw_id, user_id, grade):
    r = requests.put(print_uri("/api/v1/courses/:course_id/assignments/:assignment_id/submissions/:user_id",
                               {'course_id': course, 'assignment_id': hw_id, 'user_id': user_id}),
                     headers=HEADERS,params={'submission[posted_grade]':grade})
    success = r.status_code == requests.codes.ok

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





def get_students(accessor,courseID=None):

    if not courseID:
        courseID = accessor.courseID

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn("no Canvas course associated with courseID %d",courseID)
        return []


    students = canvas_get_students(course)
    
    net_ids = [s['net_id'] for s in students]

    mechta_users = accessor.get_all_users(courseID=courseID)

    mechta_ids = {u['username']:u['userID'] for u in mechta_users}
    
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

def get_mechta_to_canvas_student_ids(accessor,courseID=None):
    return mechta_to_canvas_student_ids(get_students(accessor,courseID=courseID))

def canvas_get_studentIDs(course):
    students = get_paginated(print_uri("/api/v1/courses/:course_id/students",
                            {'course_id': course}), HEADERS)

    if 'errors' in students:
        logger.warn("error loading students from canvas")
        return []

    studentIDs = [s['sis_login_id'] for s in students]

    return studentIDs


def canvas_get_students(course):
    students = get_paginated(print_uri("/api/v1/courses/:course_id/students",
                               {'course_id': course}), HEADERS)

    if 'errors' in students:
        logger.warn("error loading students from canvas")
        return []
    
    students = [{'net_id':s['login_id'],'canvas_id':s['id']} for s in students]

    return students

def canvas_get_users(course,enrollment_type=None):
    if enrollment_type:
        params= {'enrollment_type':enrollment_type}
    else:
        params = {}
    params['include[]'] = 'email'
    students = get_paginated(print_uri("/api/v1/courses/:course_id/users",{'course_id': course}), HEADERS, params)

    return students

def canvas_user_to_mechta_user(c_user,user_type='student'):

    (last,first) = c_user['sortable_name'].split(', ')

    mta_user = {u'firstName': first,
                u'lastName': last,
                u'studentID': c_user['id'],
                u'userType': user_type, # 'instructor'
                u'username': c_user['sis_login_id']}

    return mta_user

#{u'id': 24983,
#  u'integration_id': None,
#  u'login_id': u'jma771',
#  u'name': u'John Albers',
#  u'short_name': u'John Albers',
#  u'sis_login_id': u'jma771',
#  u'sis_user_id': u'jma771',
#  u'sortable_name': u'Albers, John'}

def canvas_import_users_to_mechta(accessor,courseID=None):

    if not courseID:
        courseID=accessor.courseID

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        return False

    # all canvas users
    mta_users = get_canvas_users_for_mechta(course)

    return accessor.create_users(list_of_users=mta_users)


def get_canvas_users_for_mechta(course):
    c_students = canvas_get_users(course,enrollment_type='student')
    c_instructors = canvas_get_users(course,enrollment_type='teacher') + canvas_get_users(course,enrollment_type='ta')

    mta_students = [canvas_user_to_mechta_user(c_user,user_type='student') for c_user in c_students if 'sis_login_id' in c_user]
    mta_instructors = [canvas_user_to_mechta_user(c_user,user_type='instructor') for c_user in c_instructors if 'sis_login_id' in c_user]

    # see if some users are invalid
    invalid = [c_user for c_user in c_students + c_instructors if 'sis_login_id' not in c_user]
    if invalid:
        logger.warn('some users could not be added to MechTA because they do not have NetIDs on Canvas %s',str(invalid))

    # all canvas users
    mta_users = mta_instructors + mta_students 

    return mta_users

def canvas_mechta_user_update(accessor,courseID=None):
    if not courseID:
        courseID=accessor.courseID

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn("unable to get canvas course ID for courseID %d",courseID)
        return False

    logger.info("updating MechTA course %d with Canvas course %d",courseID,course)

    (added_users,dropped_users) = canvas_mechta_user_diff(accessor,courseID=courseID)

    logger.info("adding %d users; dropping %d users.",len(added_users),len(dropped_users))

    dropped = [u['userID'] for u in dropped_users]

    success = True

    if dropped:
        r = accessor.delete_users(users = dropped, courseID=courseID)
        if r.ok:
            logger.info("successfully dropped users")
        else:
            success = False


    if added_users:
        r = accessor.create_users(list_of_users=added_users,courseID=courseID)
        if r.ok:
            logger.info("successfully added users")
        else:
            success = False


    return success
        
    

def canvas_mechta_user_diff(accessor,courseID=None):

    if not courseID:
        courseID=accessor.courseID

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        return []


    logger.info("diffing users in Canvas Course %s and MechTA Course %s",course,courseID)

    # all canvas users
    canvas_users = get_canvas_users_for_mechta(course)
    if not canvas_users:
        logger.error("no canvas users, probably canvas is not properly configured, aborting")
        return ([],[])
    

    canvas_usernames = [u['username'] for u in canvas_users]

    # current mta users
    mta_users = accessor.get_all_users(courseID=courseID)
    mta_users = [u for u in mta_users if u['userType'] == 'student' or u['userType'] == 'instructor']
    mta_usernames = [u['username'] for u in mta_users]

    # dropped mta users
    dropped = accessor.get_dropped_students(courseID=courseID)

    added_users = [u for u in canvas_users if u['username'] not in mta_usernames]
    dropped_users = [u for u in mta_users if u['username'] not in canvas_usernames and u['userID'] not in dropped]

    logger.info("Added %d users",len(added_users))
    logger.info("Dropped %d users",len(dropped_users))

    return (added_users,dropped_users)



def get_dropped_users(accessor,courseID=None):
    (_,dropped_users) = canvas_mechta_user_diff(accessor,courseID=courseID)

    return [u['userID'] for u in dropped_users]




##
## CREATE & LIST ASSIGNMENTS and ASSIGNMENT GROUPS on CANVAS
##

def canvas_get_assignment_groups(course):
    groups = get_paginated(print_uri("/api/v1/courses/:course_id/assignment_groups",
                               {'course_id': course}), HEADERS)
    return groups



def canvas_new_assignment(course,name,assignment_group_id = None,position=None,published=False,points_possible=100):
    data = {'assignment':{
            'name':name,
            'points_possible':points_possible,
            'grading_type':'percent',
            'published':published,
            'submission_types':['none']
        }}
    if position:
        data['assignment']['position'] = position

    if assignment_group_id:
        data['assignment_group_id'] = assignment_group_id

    
    params = {'course_id':course}
    
    r = requests.post(print_uri("/api/v1/courses/:course_id/assignments",params),headers=HEADERS,json=data)

    if not r.ok:
        logger.warn("unable to create assignment in course")
        logger.debug("%s",r.text)
        return None

    return r.json()['id']

def canvas_upload_submission_zero_grades(accessor,assignmentID,assignments,mechta_to_canvas,submission_bonus,courseID=None):


    if not courseID:
        courseID = accessor.get_courseID(assignmentID)

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn("No canvas course number associated with courseID %d",courseID)
        return False



    submitters = accessor.peermatch_get_peer_ids(assignmentID)

    students = mechta_to_canvas.keys()
    
    non_submitters = list(set(students) - set(submitters))

    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]    
    # add essay grades grade
    for i in non_submitters:
        g = submission_bonus  # give non-submitters the no-appeal bonus.

        canvas_uid = mechta_to_canvas[i]

        print "setting submission grade on assignment " + str(assn['canvas_submission_id']) + " for student " + str(canvas_uid) + " to " + str(g)
        canvas_set_grade(course,assn['canvas_submission_id'],canvas_uid,g)   
  
    


def canvas_upload_submission_grades(accessor,assignmentID,assignments,mechta_to_canvas,bonus,appeals_only=False,courseID=None):


    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn("No canvas course number associated with courseID %d",courseID)
        return False

    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]

    canvas_id = assn['canvas_submission_id']

    if not canvas_id:
        logger.warn("Unable to upload submission grades for assignment %d.  No corresponding Canvas assignment",assignmentID)

        return False

    subgrades = accessor.get_submission_grades(assignmentID,courseID=courseID)
    subgrades = [(d['studentID'],d['submissionID'],d['grade']) for d in subgrades]

    submitters = [i for (i,_,_) in subgrades]
    students = mechta_to_canvas.keys()    
    non_submitters = list(set(students) - set(submitters))
    
    # add zero + bonus for non-submitters to subgrades
    if not appeals_only:
        subgrades += [(i,-1,bonus) for i in non_submitters]


    logger.info("\nUploading submission grades for:\n"
                   + "\tName: %s\n"
                   + "\tMechTA ID: %s\n"
                   + "\tCanvas Review ID: %s\n",
                assn['name'],assn['mechta_id'],canvas_id)


    # filter out grades that are not appealed.
    if appeals_only:
        appealed_submissions = accessor.get_appeal_submissions(assignmentID,courseID=courseID)
        subgrades = [(uid,sid,g) for (uid,sid,g) in subgrades if sid in appealed_submissions]


    # add essay grades grade
    for (i,j,g) in reversed(subgrades):
        
        if i in mechta_to_canvas:

            canvas_uid = mechta_to_canvas[i]
            logger.info("setting submission grade on assignment "
                        + "%d for student %d to %f",
                        canvas_id,canvas_uid,g)  
            canvas_set_grade(course,canvas_id,canvas_uid,g)   
        else:
            logger.warn("MechTA student %d is not in Canvas",i)

    return True


def canvas_upload_review_grades(accessor,assignmentID,assignments,mechta_to_canvas,courseID=None):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)

    course = get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not course:
        logger.warn("No canvas course number associated with courseID %d",courseID)
        return False


    # dictionary to map to canvas assignment ids.
    assn = [assn for assn in assignments if assn['mechta_id'] == assignmentID][0]

    canvas_id = assn['canvas_review_id']
    if not canvas_id:
        logger.warn("Unable to upload review grades for assignment %d.  No corresponding Canvas assignment",assignmentID)
        return False


    revgrades = accessor.get_peerreview_grades(assignmentID,courseID=courseID)
    
    # grade is the maximum review score.
    revgrades = tuples_to_kkv([(d['reviewerID'],d['submissionID'],d['grade']) for d in revgrades])
    revgrades = [(i,max(jtog.values())) for i,jtog in revgrades.items()]
    
    


    logger.info("\nUploading peer review grades for:\n"
                   + "\tName: %s\n"
                   + "\tMechTA ID: %s\n"
                   + "\tCanvas Review ID: %s\n",
                assn['name'],assn['mechta_id'],canvas_id)
    
    # add essay grades grade
    for (i,g) in revgrades:
        if i in mechta_to_canvas:
            canvas_uid = mechta_to_canvas[i]
            logger.info("setting review grade on assignment "
                        + "%d for student %d to %f",
                        canvas_id,canvas_uid,g)  
            canvas_set_grade(course,canvas_id,canvas_uid,g)   
        else:
            logger.warn("MechTA student %d is not in Canvas",i)

    return True


def canvas_upload_grades(accessor,assignmentID,assignments,mechta_to_canvas,submission_bonus,appeals_only=False,courseID = None):

    if not courseID:
        courseID = accessor.get_courseID(assignmentID)

    success = canvas_upload_submission_grades(accessor,assignmentID,assignments,mechta_to_canvas,submission_bonus,appeals_only=appeals_only,courseID=courseID)

    if not appeals_only and success:
        success = canvas_upload_review_grades(accessor,assignmentID,assignments,mechta_to_canvas,courseID=courseID)

    return success
    
def get_emails(accessor,courseID=None):
    if not courseID:
        courseID=accessor.courseID

    canvas_id = get_canvas_course_from_accessor(accessor,courseID=courseID)
    
    if not canvas_id:
        logger.warn("No canvas course number associated with courseID %d",courseID)
        return {}

    login_to_email = {d['sis_login_id']:d['email'] for d in canvas_get_users(canvas_id) if 'sis_login_id' in d}
    login_to_id = {d['username']:d['userID'] for d in accessor.get_all_users(courseID=courseID)}

    id_to_email = {login_to_id[login]:login_to_email[login] for login in login_to_id.keys() if login in login_to_email}

    return id_to_email

    

    


