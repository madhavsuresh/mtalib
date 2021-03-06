from __future__ import division
from util import *
from math import sqrt

MIN_VARIANCE = 0.001    # don't let 1/variance blow up if a peer is very accurate.
DEFAULT_VARIANCE = 1.0  # this does not matter as long as it is the same.

def safe_divide(num,denom,infinity):
    return min(num / denom,infinity) if denom != 0 else infinity 



# assign students in groups to k submissions.
#    reviews:     {'peer name' => {'submission name' => score} 
#    truth:       {'submission name'=> score}
#    t:           number of iterations after which to quit.
# returns:
#    (scores,qualities): ({submission=>(score,var)},{peer=>var})
def simple_vancouver(reviews, truth, t):
    # i: peers; j: submissions

    # strip scores 
    #   iassign[i] = submissions assigned to peer i
    #   jassign[j] = peers assigned to review submission j
    iassign = {i: review.keys() for (i, review) in reviews.items()}
    jassign = invert_dictlist_dup(iassign)

    peers = iassign.keys()
    submissions = jassign.keys()

    # ivar[i] and jvar[j] are 1/variance
    jvar = {j: 1.0 / DEFAULT_VARIANCE for j in submissions}
    jmean = {j: 0.0 for j in submissions}
    ivar = {i: 1.0 / DEFAULT_VARIANCE for i in peers}

    for _ in range(t):
        # update score ivariances: jvar[j] = sum_i ivar[i]
        #    notes: ignores old ivar
        jvar = {j: sum([ivar[i] for i in jassign[j]]) for j in submissions}

        # update score mean: jmean[j] = (sum_i reviews[i,j] ivar[i]) / jvar[j]] 
        jmean = {j: sum([reviews[i][j] * ivar[i] for i in jassign[j]]) / jvar[j] for j in submissions}

        # reset the truth.
        jmean.update(truth)

        # update qualities: ivar[i] = (sum_j jvar[j]) / (sum_j jvar[j](reviews[i][j]-jmean[j]))
        ivar = {i: safe_divide(
                       sum([jvar[j] for j in iassign[i]]),
                       sum([jvar[j] * (reviews[i][j] - jmean[j]) ** 2 for j in iassign[i]]),
                       1/MIN_VARIANCE)
                   for i in peers}

    scores = {j: (jmean[j], 1.0 / jvar[j]) for j in submissions}
    quality = {i: 1.0 / ivar[i] for i in peers}

    return (scores, quality)


# assign students in groups to k submissions.
#    reviews:     {'peer name' => {'submission name' => score} 
#    truth:       {'submission name'=> score}
#    t:           number of iterations after which to quit.
# returns:
#    (scores,qualities): ({submission=>(score,var)},{peer=>var})
# PRECONDITIONS:
#    - peers assigned to at least two submissions.
#    - submissions assigned to at least two peers.
# NOTES:
#    - runs exactly t iterations.  does not stop if no improvements.
def vancouver(reviews, truth, t):
    # i: peers; j: submissions
    reviews = ensure_kkv(reviews)

    # strip scores 
    #   iassign[i] = submissions assigned to peer i
    #   jassign[j] = peers assigned to review submission j
    iassign = {i: review.keys() for (i, review) in reviews.items()}
    jassign = invert_dictlist_dup(iassign)

    # make sure preconditions are met
    kmin = min(len(subs) for (i, subs) in iassign.items())
    assert kmin >= 2, "Vancouver needs at least two submissions per peer!"
    lmin = min(len(peers) for (j, peers) in jassign.items())
    assert lmin >= 2, "Vancouver needs at least two peers per submission!"

    peers = iassign.keys()
    submissions = jassign.keys()

    # maintain ivar, jvar, jmean for each edge in assignment
    # ivar and jvar are 1/variance!
    ivars = {i: {j: 1.0 / DEFAULT_VARIANCE for j in iassign[i]} for i in peers}
    jvars = {i: {j: 1.0 / DEFAULT_VARIANCE for j in iassign[i]} for i in peers}
    # jmean = {i: {j: avg([reviews[ii][j] for ii in jassign[j] if ii != i]) for j in iassign[i]} for i in peers}
    jmeans = {i: {j: 1.0 for j in iassign[i]} for i in peers}

    for _ in range(t):
        # update score inverse variances for submissions
        jvars = {i: {j: sum([ivars[ii][j] for ii in jassign[j] if ii != i]) for j in iassign[i]} for i in peers}

        # update score mean: jmean[j] = (sum_i reviews[i,j] ivar[i]) / jvar[j]] 
        jmeans = {i: {j: truth[j] if j in truth \
            else sum([reviews[ii][j] * ivars[ii][j] for ii in jassign[j] if ii != i]) / jvars[i][j] \
                      for j in iassign[i]} \
                  for i in peers}

        # update qualities: ivar[i] = (sum_j jvar[j]) / (sum_j jvar[j](reviews[i][j]-jmean[j]))
        ivars = {i: {j: safe_divide(
                            sum([jvars[i][jj] for jj in iassign[i] if jj != j]),
                            sum([jvars[i][jj] * (reviews[i][jj] - jmeans[i][jj]) ** 2 for jj in iassign[i] if jj != j]),
                            1 / MIN_VARIANCE)
                     for j in iassign[i]}
                 for i in peers}

    # update score ivariances: jvar[j] = sum_i ivar[i]
    #    notes: ignores old ivar
    jvar = {j: sum([ivars[i][j] for i in jassign[j]]) for j in submissions}

    # update score mean: jmean[j] = (sum_i reviews[i,j] ivar[i]) / jvar[j]] 
    jmean = {j: sum([reviews[i][j] * ivars[i][j] for i in jassign[j]]) / jvar[j] for j in submissions}

    # reset the truth.
    jmean.update(truth)

    # update qualities: ivar[i] = (sum_j jvar[j]) / (sum_j jvar[j](reviews[i][j]-jmean[j]))
    ivar = {i: safe_divide(
                   sum([jvars[i][j] for j in iassign[i]]),
                   sum([jvars[i][j] * (reviews[i][j] - jmeans[i][j]) ** 2 for j in iassign[i]]),
                   1 / MIN_VARIANCE)
            for i in peers}

    scores = {j: (jmean[j], 1.0 / jvar[j]) for j in submissions}
    quality = {i: 1.0 / ivar[i] for i in peers}

    return (scores, quality)


def vancouver_preconditions(reviews,truths,t=0):
    reviews = ensure_kkv(reviews)
    # strip scores 
    #   iassign[i] = submissions assigned to peer i
    #   jassign[j] = peers assigned to review submission j
    iassign = {i: review.keys() for (i, review) in reviews.items()}
    jassign = invert_dictlist_dup(iassign)

    kmin = min(len(subs) for (i, subs) in iassign.items())
    lmin = min(len(peers) for (j, peers) in jassign.items())

    return kmin >=2 and lmin >= 2

# compares vancouver weighted scores to scores from truths.
# vancouver sets final score to truth, so this needs to redo the last round 
# of vancouver.
def vancouver_errors(reviews,truths,scores,qualities,tas = []):
    
    #{j:{i:score,...},...}
    subreviews = kkv_invert(reviews)
    
    submissions = subreviews.keys()

    def meanvar(valsweights):
        (_,weights) = zip(*valsweights)
        
        total_weight = sum(weights)

        mean = sum([val*weight for (val,weight) in valsweights])/total_weight
        
        var = sum([((val - mean)**2 * weight) for (val,weight) in valsweights])/total_weight

        return (mean,var)
        

    peerscores = {j:meanvar([(s,1/qualities[i])  for i,s in subreviews[j].items() if i not in tas])
                  for j in submissions} 

    withouttruths = [j for j in submissions if j not in truths]
    withtruths = truths.keys()

    
    errors_withtruth = {j:abs(peerscores[j][0] - truths[j]) for j in withtruths if j in peerscores}
    errors_withouttruth = {j:sqrt(peerscores[j][1]) for j in withouttruths if j in peerscores}

    return errors_withtruth,errors_withouttruth

