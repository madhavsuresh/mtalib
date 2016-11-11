from mtalib.api import api
from mtalib.algo.util import *
from pprint import pprint

def rubric_questions(accessor,assignmentID):
    r = accessor.get_rubric(assignmentID)

    
    qs =[(q,d.get('weight',None),d['name'],d['question']) for q,d in r.items()]
    
    qs.sort(key=(lambda (q,a,b,c): r[q]['displayPriority']),reverse=True)
    
    return ([q for (q,_,_,_) in qs],qs)

def rubric_update_questions(accessor,assignmentID,rubric):
    for q,d in rubric:
        accessor.update_rubric_question(assignmentID,**d)
        
    return True

def rubric_set_order(accessor,assignmentID,questions):
    r = accessor.get_rubric(assignmentID)
    qs = r.keys()
        
    priority = {q:i for q,i in zip(questions,range(len(questions)))}
    print priority
    
    def key(q):
        return (priority.get(q,len(priority)+1),q)
    
    qs.sort(key=key)
    
    print qs
    
    for q,p in zip(qs,range(len(qs),0,-1)):
        logger.warn("question %d to priority %d",q,p)
        accessor.update_rubric_question(assignmentID,q,displayPriority=p)
                 
    return True




# run with weights={} to see rubric questions.
def update_rubric_weights(accessor,assignmentID,weights={}):
    rubric = accessor.get_rubric(assignmentID=assignmentID)
    pprint({q:r['name'] for q,r in rubric.items() if 'weight' in r})
    print 'old weights'
    pprint({q:r['weight'] for q,r in rubric.items() if 'weight' in r})

    if not weights:
        return
    
    for q,w in weights.items():
        rubric[q]['weight'] = w 


    for q,w in weights.items():
        accessor.update_rubric_question(assignmentID=assignmentID,questionID=q,weight=w)

    print 'new weights'
    updated_rubric = accessor.get_rubric(assignmentID)
    pprint({q:r['weight'] for q,r in updated_rubric.items() if 'weight' in r})
    print "total weight: " + str(sum([w for w in weights.values()]))


rubric_question_defaults = {
    'name':'Default question', 
    'question':'Default question text.', 
    'hidden':0, 
    'displayPriority':0, 
    'weight':10,
    'options':   [{'label' : '10' , 'score' : 1.0}, 
                  {'label' : '9' , 'score' : 0.9}, 
                  {'label' : '8' , 'score' : 0.8}, 
                  {'label' : '7' , 'score' : 0.7}, 
                  {'label' : '6' , 'score' : 0.6}, 
                  {'label' : '5' , 'score' : 0.5}, 
                  {'label' : '4' , 'score' : 0.4}, 
                  {'label' : '3' , 'score' : 0.3}, 
                  {'label' : '2' , 'score' : 0.2}, 
                  {'label' : '1' , 'score' : 0.1}, 
                  {'label' : '0' , 'score' : 0.0},                   
                  {'label' : 'Skip', 'score' : -0.1}]
}

def create_rubric_question(accessor,assignmentID,courseID=None,defaults=rubric_question_defaults,**kwargs):
    return accessor.create_rubric_question(assignmentID,courseID=courseID,defaults=defaults,**kwargs)




# FORMAT FOR 'text':
# """POINTS:  QUESTION NAME 1: QUESTION DESCRIPTION 1
#    POINTS: QUESTION NAME 2: QUESTION DESCIPTION 2
#    ...
#    POINTS: QUESTION NAME K: QUESTION DESCIPTION K"""
# Notes:
#    - there is no API to delete rubric quesstions, 
#      so they must be manually deleted first.
#      (this raises an exception if existing rubric is longer then update)
def update_rubric(accessor,assignmentID,text):
    
    questions = text.strip().split("\n")

    wnqs = [nq.split(":",2) for nq in questions]

    wnqs = [(int(w.strip()),n.strip(),q.strip()) for (w,n,q) in wnqs]

    print "total points: " + str(sum([w for (w,_,_) in wnqs]))

    rubric = accessor.get_rubric(assignmentID=assignmentID)
    score_qs = [q for (q,r) in rubric.items() if 'options' in r]

    if len(score_qs) > len(wnqs):
        print "manually delete " + str(len(score_qs)-len(wnqs)) + " questions"
        raise
    if len(score_qs) < len(wnqs):
        for _ in range(len(wnqs)-len(score_qs)):
            print "adding question"
            create_rubric_question(accessor,assignmentID=assignmentID)
        rubric = accessor.get_rubric(assignmentID=assignmentID)
        score_qs = [q for (q,r) in rubric.items() if 'options' in r]
        if len(score_qs) != len(wnqs):
            print "failed to add questions"
            raise

    update_tuples = {q:wnqs for q,wnqs in zip(score_qs,wnqs)}



    update = {q:{'name':n,'question':qq,'weight':w} for q,(w,n,qq) in update_tuples.items()}

    print "updating questions"
    for q,d in update.items():
        accessor.update_rubric_question(assignmentID=assignmentID,questionID=q,**update[q])


    feedback_q = [q for q,r in rubric.items() if r['name'] == 'Feedback'][0]
    justification_q = [q for q,r in rubric.items() if r['name'] == 'Justification'][0]

    ordered_qs = [feedback_q] + score_qs + [justification_q]
    print "setting order: " + str(ordered_qs)
    rubric_set_order(accessor,assignmentID,ordered_qs)


    pprint(rubric_questions(accessor,assignmentID=assignmentID))

    
def update_rubric_options(accessor,assignmentID):
    rubric = accessor.get_rubric(assignmentID=assignmentID)
    for q,r in rubric.items():
        if 'options' in r:
            print "updating question: " + r['name']
            accessor.update_rubric_question(assignmentID=assignmentID,questionID=q,options=rubric_question_defaults['options'])
