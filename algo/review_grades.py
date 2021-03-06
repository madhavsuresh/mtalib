from __future__ import division
from util import *
from numbers import Number
import logging

logger = logging.getLogger('mtalib.algos.review_grades')

class NonScore:
    NO_ANSWER = None
    SKIP = None
    
    def __str__(self):
        return 'NonScore.' + self.__class__.__name__

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not self.__eq__(other)

class NO_ANSWER(NonScore):
    pass

class SKIP(NonScore):
    pass

NonScore.NO_ANSWER = NO_ANSWER()
NonScore.SKIP = SKIP()


### quadratic loss function
def linear_loss(truth, score):
    max_diff = max(1-truth,truth)

    return (abs(truth-score)/max_diff) 


### quadratic loss function
def quadratic_loss(truth, score):
    max_diff = max(1-truth,truth)

    return ((truth-score)/max_diff)**2 

###
### calculate peer review grade
### truth:            TA score in [0,1]
### score:            peer score in [0,1] (or negative for skip) 
### avg_scores:       average of TA scores in [0,1]
### skip_loss:        loss if the peer skipped the review, in [0,1].
### loss:             loss function, e.g., quadratic_loss, in [0,1]->[0,1]
def review_grade(truth,score,avg_score,skip_loss,loss=quadratic_loss):

    avg_loss = loss(truth,avg_score) 

    # loss is u-shaped, so max_loss is at endpoints.
    max_loss = max(loss(truth,1.0),loss(truth,0.0))
    
    # (if necessary) adjust skip loss to keep scores in [0,1] 
    sl = min(skip_loss,avg_loss/max_loss)
    if sl != skip_loss:
        logger.info('skip_loss set to %s',sl)
    skip_loss = sl

    
    # if peer skipped the question then loss is skip_loss.
    if score == NonScore.SKIP:
        return 1.0 - skip_loss
    # if peer didn't answer then loss is total.
    if score == NonScore.NO_ANSWER:
        return 0.0
    if isinstance(score,Number):
        return (1.0 - loss(truth,score) * skip_loss / avg_loss) if avg_loss > 0.0 else 1.0

    logger.error('Invalid score for peer review grading: %s.',score)
    return 0.0

# assign students in groups to k submissions.
#    reviews:     {'peer name' => {'submission name' => score} 
#    truths:      {'submission name'=> score}
#    skip_loss:   loss if the peer skipped the review, in [0,1].
#    loss:        function for calculating loss (out of 1)
# returns:
#    grades:      [(i,j,grade),...]
def review_grades(reviews, truths, skip_loss,loss=quadratic_loss):
    reviews = ensure_tuples(reviews)
    # i: peers; j: submissions

    # for each submission that is TA graded,
    # grade the peer versus the TA.
    # a peer's final grade is the average of the 

    peers = set([i for (i,_,_) in reviews])
    graded_submissions = truths.keys()
    avg_score = avg(truths.values())

    # select the reviews for which there is ground truth.
    graded_reviews = [(i,j,s) for (i,j,s) in reviews if j in graded_submissions]


    # grade each review for which there is ground truth.
    grades = [(i,j,review_grade(truths[j],score,avg_score,skip_loss,loss)) for (i,j,score) in graded_reviews]

    return tuples_to_kkv(grades)

def peer_grades(reviews, truths, skip_loss,loss=quadratic_loss):

    ijtog = ensure_kkv(review_grades(reviews,truths,skip_loss,loss))

    # a peer's grade is the average of 
    itog = {i:avg(jtog.values()) for (i,jtog) in ijtog.items()}


    return itog
