from __future__ import division
from . import grading
from ..algo.util import *

from . import appeals
from . import upload_grades
from copy import deepcopy

import logging
logger = logging.getLogger()


job_name = 'upload_appeal_grades'
job_summary = 'Upload Appeal Grades to Canvas'


default_params = deepcopy(upload_grades.default_params)
default_params['appeals_only'] = True




def run(accessor,assignmentID,courseID=None,**params):

    courseID = accessor.get_courseID(assignmentID,courseID=courseID)


    # get parameters.
    d_params = deepcopy(default_params)
    d_params.update(params)
    a_params = accessor.get_assignment_params(assignmentID,courseID=courseID)
    d_params.update(a_params)
    params = d_params


    missing = grading.missing_truths_from_accessor(accessor,assignmentID=assignmentID,courseID=courseID)
    if missing:
        logger.warn("TA appeals have not been entered.  Appeal grades have not been uploaded.  Upload manually.")
        ta_records = key_on(accessor.get_users(courseID,users=missing.keys()),'userID')
        for ta in missing.keys():
            logger.warn("Grader %s has %d missing reviews.",ta_records[ta]['firstName'],len(missing[ta]))

        return False

    logger.info("setting submission grades according to appeals")
    if not appeals.set_appeal_grades(accessor,assignmentID,courseID=courseID):
        logger.warn("failed to set submission grades")

    return upload_grades.run(accessor,assignmentID,courseID=courseID,**params)

