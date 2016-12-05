import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.isotonic import IsotonicRegression

'''
Whole file is deprecated since it uses db file instead of api call. Included just in case of helpful functions
'''


#Calculate number of instances where peer score matches TA score
def sameCount(data):
    count = 0;
    total = 0;
    for i in range(len(data['score'])):
        if (data['score'][i] == data['scoreSum'][i]):
            count += 1;
        total += 1;
        
    print count, total

#Plot the variance/std of peer scores vs TA score    
def statistics(data):
    values = [None]*100
    
    for i in range(100):
        values[i] = []
        
    for j in range(len(data['score'])):
        values[int(data['score'][j]-1)].append(data['scoreSum'][j])
    
    stdDevs = [None]*100
    variances = [None]*100
    yaxis = [None]*100


    for k in range(len(values)):
        stdDevs[k] = np.std(values[k])
        variances[k] = np.std(values[k])
        yaxis[k] = k*100/30
       
    plt.plot(variances, linestyle='',marker= 'o')
    plt.xlabel('TA Score')
    plt.ylabel('Average')

#Plot all instances of peer score vs TA score    
def scoreAccuracy(data):
    plt.scatter(data['score'],data['scoreSum'],alpha=.1)
    


def isoReg(data):
    ir = IsotonicRegression()
    x = data['score']
    q = data['scoreSum']
    y = ir.fit_transform(data['score'],data['scoreSum'])
    
    order = np.argsort(x)
    xs = np.array(x)[order]
    ys = np.array(y)[order]
    
    plt.plot(xs,ys,color='r')
    plt.plot([0,100],[0,100])
    
    print ir.score(x,q)
    
#main function is deprecated since it uses SQL query instead of api call    
'''
def main():
    dbFile = '/Users/Hosung/Dropbox/School/#2016/399/mta_sqlite_db.db'
    
    con = sqlite3.connect(dbFile)
    
    query = """SELECT peer_review_assignment_submissions.submissionID,
                      peer_review_assignment_matches.matchID,score,scoreSum,reviewerID
            FROM users 
            JOIN peer_review_assignment_submissions 
                on users.userID = peer_review_assignment_submissions.authorID 
            NATURAL JOIN peer_review_assignment_submission_marks 
            NATURAL JOIN peer_review_assignment_matches
            NATURAL JOIN 
                (SELECT matchID, SUM(score) as scoreSum
                    FROM peer_review_assignment_review_answers 
                        JOIN peer_review_assignment_radio_options 
                            ON peer_review_assignment_radio_options.questionID = peer_review_assignment_review_answers.questionID
                                AND peer_review_assignment_radio_options."index" = peer_review_assignment_review_answers.answerInt
                        GROUP BY matchID) AS peerScores
            WHERE reviewerID IN ( 282,284,286,287,316,317 )
            ORDER BY peer_review_assignment_submissions.submissionID ASC
            """

    data = pd.read_sql_query(query,con)
    print data
    scoreAccuracy(data);
    sameCount(data);
    isoReg(data)
    title = 'Distribution of All Scores > 70 (alpha=0.1)'
    plt.title(title)
    plt.axis([50.0,100.0,50.0,100.0])
    plt.xlabel('TA Scores')
    plt.ylabel('PR Scores')
    plt.savefig('distributionAll70')
    plt.show()
'''    