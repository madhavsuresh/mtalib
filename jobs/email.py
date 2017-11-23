from ..algo.util import *

from pprint import pprint
from copy import deepcopy

import string
import smtplib

import logging
logger = logging.getLogger()








def send(recipient, subject, body, sender='Mechanical TA <nu.mech.ta@gmail.com>',user='nu.mech.ta@gmail.com', pwd='numechtaemailer'):

    if not sender:
        sender = user
    
    gmail_user = user
    gmail_pwd = pwd
    
    params = {
        'FROM': sender,
        'TO': recipient.join(', ') if type(recipient) is list else recipient,
        'SUBJECT': subject,
        'BODY': body
        }

    
    # Prepare actual message
    message = string.Template("""\
From: $FROM
To: $TO
Subject: $SUBJECT

$BODY\
""").substitute(params)
    
  
    success = True
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(params['FROM'],params['TO'], message)
        server.close()
        logger.info('SENT MESSAGE')
        logger.info("%s",message)
    except Exception as e:
        logger.warn("failed to send mail")
        logger.warn("error: %s",str(e))
        success = False

    return success
