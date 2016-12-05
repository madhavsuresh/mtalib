import sqlite3
import pandas as pd
import numpy as np
from ..api.api import *
import mlutil

'''
Future considerations:
    Currently the file is a mix of SQL queries and api calls, here is everything that doesn't use the api:
        -Getting question and submission text (uses queries from sqlite db file since no endpoint currently exists for them)
        -Getting questionIDs for writing quality scores (this is currently done manually when 
                                                         initializing mltext.assignmentList and mltext.writingQualityQuestions)
        -mltext.dbreviews() (deprecated)
'''


#the purpose of this class is to maintain data across different functions to avoid having to pass them as arguments
class mltext:
    assignmentList = []
    writingQualityQuestions = []
    dbreader = None
    taList = None
    data = pd.DataFrame()
    features = pd.DataFrame()
    keys = pd.DataFrame()
    dbFile = None
    c = None
    questiontext = []
    
    
    def __init__(self,url,un,pw):
        self.assignmentList = [1,4,5,6,7,8,9,10,11,12]
        self.writingQualityQuestions = [0,8,0,0,19,37,48,53,62,80,75,82,92]
        self.dbreader = api.server_accessor(url, username=un, password=pw)
        self.taList = [282,284,286,287,316,317]
        self.dbFile = 'insert db file directory here'
        self.con = sqlite3.connect(self.dbFile)
        self.c = self.con.cursor()
        self.questiontext = self.get_questions()
        
    #Get and parse the text of each assignment question    
    def get_questions(self):
        query = """SELECT assignmentID,submissionQuestion FROM peer_review_assignment"""
        questiondata= pd.read_sql_query(query,self.con)
        questiondata['text'] = questiondata['submissionQuestion']
        questiondata = querydb.parseText(questiondata)
        questiondata = questiondata.drop('wordCount',1)
        return questiondata['parsed']
   
    #Write JSON reviews from database to dataframe
    #subset values:
    def reviews_to_pandas(self):
        qualities = []
        submissions = []
        assignmentNo = []
        reviewers = []
        isTa = []
        
        for i in self.assignmentList:
            reviews = self.dbreader.get_peerreviews(i)
            for submission in reviews:
                for pr in reviews[submission]:
                    try:
                        qualities.append(10-int(pr['answers'][self.writingQualityQuestions[i]]['int']))
                        submissions.append(pr['submissionID']['id'])
                        assignmentNo.append(i)
                        reviewers.append(pr['reviewerID']['id'])
                        isTa.append(bool(int(pr['reviewerID']['id']) in self.taList))
                            
                    except KeyError:
                        #print "Derp " + str(pr['answers'])
                        pass
    
        self.data['quality'] = pd.Series(qualities)
        self.data['submissionID'] = pd.Series(submissions)
        self.data['assignmentID'] = pd.Series(assignmentNo)
        self.data['reviewerID'] = pd.Series(reviewers)
        self.data['isTa'] = pd.Series(isTa)
    
    
    #Get reviews from SQL database and invert quality scores, then put in dataframe. Currently deprecated.
    '''    
    def dbreviews(self, tasonly):
        taQuality = """SELECT submissionID, answerInt, score, reviewerID, assignmentID    
            FROM peer_review_assignment_matches
            NATURAL JOIN peer_review_assignment_review_answers
            NATURAL JOIN peer_review_assignment_submission_marks
            NATURAL JOIN peer_review_assignment_questions
            WHERE questionID IN ( 8,19,37,48,53,62,80,75,82,92 )
            AND reviewerID IN ( 282,284,286,287,316,317 )
            ORDER BY submissionID
            """
        allQuality = """SELECT submissionID, answerInt, score, reviewerID, assignmentID       
            FROM peer_review_assignment_matches
            NATURAL JOIN peer_review_assignment_review_answers
            NATURAL JOIN peer_review_assignment_submission_marks
            NATURAL JOIN peer_review_assignment_questions
            WHERE questionID IN ( 8,19,37,48,53,62,80,75,82,92 )
            ORDER BY submissionID
            """
            
        qualities = []

        if (tasonly == 1):
            self.data = pd.read_sql_query(taQuality, self.con)
        else:
            self.data = pd.read_sql_query(allQuality, self.con)
        for index,rows in self.data.iterrows():
            qualities.append(10-int(rows['answerInt']))
        self.data['quality'] = pd.Series(qualities)
    '''    
        
    #Get each submission's text from the database    
    def get_all_submission_text(self):
        text = []
        for index,rows in self.data.iterrows():
            text.append(self.get_individual_submission_text(str(rows['submissionID'])))
        self.data['text'] = text
    
    def get_individual_submission_text(self, submissionID):
        submissionText =self.c.execute("SELECT text FROM peer_review_assignment_essays WHERE submissionID = ?", (submissionID,))
        return submissionText.fetchone()[0]

    #Remove duplicate submissions
    def remove_dupes(self):
        self.data = self.data.drop_duplicates(subset = ['submissionID'])
    
    #Calculate standard deviation of peer-assignend writing quality scores across all peer reviews, then prints them
    def quality_deviation(self):
        values = []
        total = []
        current = 0
        for index,rows in self.data.iterrows():
            if (rows['submissionID'] != current):
                print current, np.std(values)
                total.append(np.std(values))
                values = []
                current = rows['submissionID']
            else:
                values = np.append(values, rows['quality'])
        total = np.array(total)
        total = total[~np.isnan(total)]
        print np.average(total)

    def sentence_length(self):
        sentlength = []
        for index,rows in self.data.iterrows():
            sents = rows['parsed'].split('.')
            avg = sum(len(x.split()) for x in sents)/len(sents)
            sentlength.append(avg)
        self.data['avgSentLength'] = sentlength
            
    #add the selected features depending on their type            
    def add_features(self, features, columns, arrays):
        for name in columns:
            features = np.column_stack((features,self.data[name]))
        for feature in arrays:
            features = np.column_stack((features, feature))
        return features
    
    #add jaccard coefficients to the feature set
    def jaccard_coefficients(self):
        jaccards = []
        for index,rows in self.data.iterrows():
            jaccards.append(self.jaccard(set(self.questiontext[rows['assignmentID']+1]),set(rows['parsed'])))
        self.data['jaccard'] = pd.Series(jaccards)

    def jaccard(self, question, answer):
        n = len(question.intersection(answer))
        return n/float(len(question)+len(answer)-n)

def is_member(checkItem, checkSet):
    L1 = [checkItem]
    return [i for i in L1 if i in checkSet]

        
        
def main():    
    #initialize server connector and mltext object
    ml = mltext('http://enron.cs.northwestern.edu/~madhav/treftun/mta/api/','root','password')
    
    #get data and put into dataframe
    ml.reviews_to_pandas()
    ml.remove_dupes()
    ml.get_all_submission_text()
    
    #create text features    
    ml.data = mlutil.parseText(ml.data)    
    ml.sentence_length()
    ml.jaccard_coefficients()
    ml.data = ml.data.dropna()
    bagofwords = mlutil.bag_of_words(ml.data['parsed'])
    bagofbigrams = mlutil.bag_of_bigrams(ml.data['parsed'])
    
    #make feature set from data to pass to classifier
    features = bagofbigrams
    features = ml.add_features(features, ['wordCount','reviewerID','avgSentLength','jaccard'],[bagofwords])
    
    #run classifier (see mlutil)
    xTrain,xTest,yTrain,yTest = train_test_split(features, 
                                                 np.asarray(ml.data['quality']).tolist(),
                                                 test_size = 0.2, 
                                                 random_state = 10)
    mlutil.logisticRegression(xTrain,yTrain,xTest,yTest)
          

    
main()