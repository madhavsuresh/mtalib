import requests
from . import canvas
import logging

logger = logging.getLogger()


job_name = 'update_enrollments'
job_summary = 'Update Enrollments from Canvas'

def run(accessor,assignmentID,courseID=None):

    if not courseID:
        courseID = accessor.get_courseID(assignmentID)

    logger.info("Executing %s for courseID %d",job_name,courseID)
    
    return canvas.canvas_mechta_user_update(accessor,courseID=courseID)
    


