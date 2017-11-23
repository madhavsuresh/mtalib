from __future__ import division
from . import canvas
from . import appeals
from ..api.api import *
from ..algo.util import *


import logging
logger = logging.getLogger()


job_name = 'upload_grades'
job_summary = 'Upload Grades to Canvas'

default_params = {'submission_name': 'Problem',
                  'review_name': 'Peer Review',
                  'mechta_name': 'Problem',
                  'submission_bonus':5.0,
                  'appeals_only':False}


def run(accessor,assignmentID,courseID=None,**params):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID=courseID)
    d_params.update(a_params)
    params = d_params

    mechta_name = params['mechta_name']
    review_name = params['review_name']
    submission_name = params['submission_name']
    appeals_only = params['appeals_only']
    submission_bonus = params['submission_bonus']


    logger.info("Executing upload_grades for assignmentID %d courseID %d",assignmentID,courseID) 
    
    assignments = canvas.get_assignments(accessor,courseID=courseID,submission_name=submission_name,review_name=review_name)

    if not assignments:
        logger.warn("could not get assignments mapping between Canvas and MechTA")
        return False

    # dictionary to map to canvas assignment ids.
    assns = [assn for assn in assignments if assn['mechta_id'] == assignmentID]

    if not assns:
        logger.warn("MechTA assignment %d not found in MechTA assignment listing",assignmentID)
        return False

    assn = assns[0]



    canvas_review_id = assn['canvas_review_id']
    canvas_submission_id = assn['canvas_submission_id']
    name = assn['name']


    canvas_course = canvas.get_canvas_course_from_accessor(accessor,courseID=courseID)
    if not canvas_course:
        logger.warn("no canvas course found for course %d",courseID)
        return False

    if not canvas_review_id:
        logger.info("Found no corresponding review assignment '%s' (assignmentID %d) in Canvas.",name,assignmentID)

        canvas_review_name = name.replace(mechta_name,review_name,1)


        logger.info("Creating canvas assignment '%s' for review grades",canvas_review_name) 
        canvas_review_id = canvas.canvas_new_assignment(canvas_course,name=canvas_review_name,points_possible = assn['review_points'])

        assn['canvas_review_id'] = canvas_review_id

        if not canvas_review_id:
            logger.warn("failed to create canvas assignment %s",canvas_review_name)


    if not canvas_submission_id:
        logger.info("Found no corresponding submission assignment '%s' (assignmentID %d) in Canvas.",name,assignmentID)

        canvas_submission_name = name.replace(mechta_name,submission_name,1)


        logger.info("Creating canvas assignment '%s' for submission grades",canvas_submission_name) 
        canvas_submission_id = canvas.canvas_new_assignment(canvas_course,name=canvas_submission_name,points_possible = assn['submission_points'])

        assn['canvas_submission_id'] = canvas_submission_id

        if not canvas_submission_id:
            logger.warn("failed to create canvas assignment %s",canvas_review_name)
            

    if not canvas_submission_id or not canvas_review_id:
        logger.warn("Unable to upload grades for assignment %d.  No corresponding Canvas assignments exist or can be created.",assignmentID)
        return False

    


    mechta_to_canvas = canvas.get_mechta_to_canvas_student_ids(accessor,courseID=courseID)

    if not mechta_to_canvas:
        logger.warn("could not get student ID mapping between Canvas and MechTA")
        return False

    return canvas.canvas_upload_grades(accessor,assignmentID,assignments,mechta_to_canvas,submission_bonus,appeals_only=appeals_only,courseID=courseID)
    
