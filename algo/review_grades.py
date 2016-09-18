from __future__ import division
import peer_review_util


### quadratic loss function
def quadratic_loss(truth, score):
    return (truth-score)**2

###
### calculate peer review grade
### truth:            TA score in [0,1]
### score:            peer score in [0,1] (or negative for skip) 
### empirical_scores: distribution of TA scores in [0,1]
### skip_loss:        loss if the peer skipped the review, in [0,1].
### loss:             loss function, e.g., quadratic_loss, in [0,1]->[0,1]
def review_grade(truth,score,empirical_scores,skip_loss,loss=quadratic_loss):
    avg_loss = avg([loss(truth,s) for s in empirical_scores])

    # loss is u-shaped, so max_loss is at endpoints.
    max_loss = max(loss(truth,1.0),loss(truth,0.0))
    
    
    # (if necessary) adjust skip loss to keep scores in [0,1] 
    sl = min(skip_loss,avg_loss/max_loss)
    if sl != skip_loss:
        print "LOGGING: review_grade(...): skip_loss set to " + str(sl)
    skip_loss = sl
    
    # if peer skipped the question then loss is skip_loss.
    if score < 0.0:
        return 1.0 - skip_loss
    
    
    # need avg_loss > skip_loss (for grades to be in [0,1]: THIS NEEDS TO BE FIXED!
    if avg_loss <= 0.0:
        print "LOGGING: review_grade(...): average_loss is zero"
    
    return (1.0 - loss(truth,score) * skip_loss / avg_loss) if avg_loss > 0.0 else 1.0

# assign students in groups to k submissions.
#    reviews:     {'peer name' => {'submission name' => score} 
#    truths:      {'submission name'=> score}
#    skip_loss:   loss if the peer skipped the review, in [0,1].
#    loss:        function for calculating loss (out of 1)
# returns:
#    grades:      {'peer name' => score}
def review_grades(reviews, truths, skip_loss,loss=quadratic_loss):
    # i: peers; j: submissions

    # for each submission that is TA graded,
    # grade the peer versus the TA.
    # a peer's final grade is the average of the 
     
    peers = reviews.keys() 
    graded_submissions = truths.keys()
    empirical_scores = truths.values()
    
    # select the reviews for which there is ground truth.
    graded_reviews = [(i,j,g) for (i,j,g) in kkv_to_tuples(reviews) if j in graded_submissions]
    

    # grade each review for which there is ground truth.
    review_grades = [(i,j,review_grade(truths[j],score,empirical_scores,skip_loss)) for (i,j,score) in graded_reviews]
    ijtog = tuples_to_kkv(review_grades)
    
    # a peer's grade is the average of 
    peer_grades = {i:avg(jtog.values()) for (i,jtog) in ijtog.items()}

    # peers with no grade
    nogrades = [i for (i,jtog) in ijtog.items() if not jtog]
    
    if nogrades:
        print "LOGGING: grade_reviews(...): There are peers with no review grades: " + str(nogrades)
        
    return peer_grades
