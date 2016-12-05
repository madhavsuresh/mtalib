import sqlite3
import pandas
from bs4 import BeautifulSoup
import re
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
from sklearn import linear_model
from sklearn import svm
from gensim.models import Word2Vec
import numpy as np

#takes string and removes punctuation, markup tags, and stopwords 
def processText(text):
    bstext = BeautifulSoup(text).get_text()
    textOnly = re.sub("[^a-zA-Z]"," ",bstext)
    lowerCase = textOnly.lower().split()
    stops = set(stopwords.words("english"))
    noStopwords = [w for w in lowerCase if not w in stops]
    finalString = " ".join(noStopwords)
    return finalString

#Parent function of processText (above). Takes a dataframe column of strings and calls process text on all of them.     
def parseText(subdata):
    completeText = []
    wordCount = []
    for index,rows in subdata.iterrows():
        iParsed = processText(rows['text'])
        completeText.append(iParsed)
        wordCount.append(len(iParsed.split()))
    subdata['parsed'] = completeText
    subdata['wordCount'] = wordCount
    return subdata

#creates bag of words classifier from an Series of parsed text    
def bag_of_words(allText):
    vectorizer = CountVectorizer(analyzer = "word",
                                 tokenizer = None,
                                 preprocessor = None,
                                 stop_words = None,
                                 max_features = 10000)
    train_data_features = vectorizer.fit_transform(allText)
    return train_data_features.toarray()
    
def bag_of_bigrams(allText):
    vectorizer = CountVectorizer(analyzer = "word",
                                 ngram_range = (2,2),
                                 tokenizer = None,
                                 preprocessor = None,
                                 stop_words = None,
                                 max_features = 10000)
    train_data_features = vectorizer.fit_transform(allText)
    return train_data_features.toarray()

#the following functions create different kinds of classifiers   
def randomForest(data, scores, tData,tScores):
    forest = RandomForestClassifier(n_estimators = 100)
    forest = forest.fit(data,scores)
    showAccuracyMetrics(forest,data,scores,tData,tScores)

def neuralNetwork(data,scores,tData,tScores):
    clf = MLPClassifier(solver = 'lbfgs', alpha=1e-5, hidden_layer_sizes=(5,2), learning_rate='constant')
    clf.fit(data, scores)
    showAccuracyMetrics(clf,data,scores,tData,tScores)

def linearRegression(data,scores,tData,tScores):
    clf = linear_model.LinearRegression()
    clf.fit(data,scores)
    showAccuracyMetrics(clf,data,scores,tData,tScores)
    
def logisticRegression(data,scores,tData,tScores):
    clf = linear_model.LogisticRegression()
    clf.fit(data,scores)
    showAccuracyMetrics(clf,data,scores,tData,tScores)
    
def svmachine(data,scores,tData,tScores):
    clf = svm.SVC(kernel='linear')
    clf.fit(data,scores)
    showAccuracyMetrics(clf,data,scores,tData,tScores)

#Calculates and prints accuracy metrics for the classifier. Shared by all classifier functions    
def showAccuracyMetrics(clf, data, scores, tData, tScores):
    print "10-fold CV scores:", cross_val_score(clf, data, scores, cv = 10)
    print "Score:", clf.score(tData,tScores)
    print "RMSE: ", mean_squared_error(clf.predict(tData), tScores)

    


    
#This main function was used before mltext file existed. Deprecated
'''    
def oldmain():
    #nltk.download()
    pandas.options.mode.chained_assignment = None
    dbFile = '/Users/Hosung/Dropbox/School/#2016/399/mta.db'
    dbFile2 = '/Users/Hosung/Dropbox/School/#2016/399/mta_sqlite_db.db'
    
    con = sqlite3.connect(dbFile2)
    
    query = """SELECT * 
            FROM users 
            JOIN peer_review_assignment_submissions 
                on users.userID = peer_review_assignment_submissions.authorID 
            JOIN peer_review_assignment_submission_marks 
                on peer_review_assignment_submissions.submissionID = peer_review_assignment_submission_marks.submissionID
            JOIN peer_review_assignment_essays
                on peer_review_assignment_submissions.submissionID = peer_review_assignment_essays.submissionID
            WHERE assignmentID = 1"""

    
    data = pandas.read_sql_query(query,con)
    print data
    subdata = data[['submissionID','text','score']].T.groupby(level=0).first().T
    subdata['wordCount'] = pandas.Series()

    completeText = []

    print subdata['text'].size

    for i in range(subdata['text'].size):
        iParsed = processText(subdata['text'][i])
        completeText.append(iParsed)
        subdata['text'][i] = iParsed
        subdata['wordCount'][i] = len(iParsed.split())

    #print completeText
    
    #avgWordVectors(completeText)

    train_data_features = initializeFeatures(completeText)
    
    #print train_data_features.shape
    train_data_features = np.append(train_data_features, subdata['wordCount'],1)
    #print train_data_features.shape

    #xTrain,xTest,yTrain,yTest = train_test_split(train_data_features, np.asarray(subdata['score'], dtype = "float64").tolist(), test_size = 0.2, random_state = 10)
    
   # linearRegression(xTrain,yTrain,xTest,yTest)
'''