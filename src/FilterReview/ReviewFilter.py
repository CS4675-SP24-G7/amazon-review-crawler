import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import json
import csv
import joblib
import time

ratingDict = {}


def train_model():
    '''
    Trains the model used to predict which Amazon reviews are
    real or fake. The model is currently trained using 'fake_reviews_dataset.csv'.
    The specific Support Vector Machine algorithm used is the Support Vector
    Classifier (SVC) algorithm, as I deemed it most accurate. It tests the
    generated model at the end and prints out an accuracy score, and then saves
    the model and vectorizer into 'trained_model.pkl' and 'premade_vectorizer.pkl',
    respectively. This is only run when generating a new prediction model.
    '''

    with open("./TraningDataset.csv", 'r') as file:
        reviews = []
        labels = []
        reviews_dataset = csv.reader(file, delimiter=',')
        next(reviews_dataset)
        for row in reviews_dataset:
            reviews.append(row[3])
            if (row[2] == 'CG'):
                labels.append(0)
            elif (row[2] == 'OR'):
                labels.append(1)
            else:
                raise Exception('BIG PROBLEM')

    # if (len(reviews) == len(labels)):
    #     print(
    #         f'Worked correctly. Reviews size: {str(len(reviews))}. Labels size: {str(len(labels))}')
    # else:
    #     print(
    #         f'Did not work correctly. Reviews size: {str(len(reviews))}. Labels size: {str(len(labels))}')

    X_train, X_test, y_train, y_test = train_test_split(
        reviews, labels, test_size=0.35)

    tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
    X_test_tfidf = tfidf_vectorizer.transform(X_test)

    svm_model = SVC()
    svm_model.fit(X_train_tfidf, y_train)

    y_pred = svm_model.predict(X_test_tfidf)

    accuracy = accuracy_score(y_test, y_pred)
    # print('Accuracy:', accuracy)
    joblib.dump(svm_model, 'trainedModel.pkl')
    joblib.dump(tfidf_vectorizer, 'premade.pkl')


def get_text(file_name):
    '''
    Takes in a json file of Amazon reviews and returns a list of reviews,
    with 'title' and 'content' concatenated for each review.

    Args:
        file_name (json file): Input json file to read.

    Returns:
        list: Amazon reviews in list of strings.
    '''

    with open(file_name, "r") as file:
        data = json.load(file)

        final_reviews = []
        for item in data["data"]:

            for review in data['data'][item]:
                # print(review['title'])
                if (review['title']):
                    if str(review['title']).endswith('.') or str(review['title']).endswith('. '):
                        review_text = review['title'] + ' ' + review['content']
                        # ratingDict[review_text] = review['rating']
                    else:
                        review_text = review['title'] + \
                            '. ' + review['content']
                        # ratingDict[review_text] = review['rating']

                    # final_reviews.append(review_text)
                else:
                    review_text = '. ' + review['content']
                    # final_reviews.append('. ' + review['content'])

                final_reviews.append(review_text)

                if (item == "FIVE_STAR"):
                    # print("It is here!!")
                    ratingDict[review_text] = 5
                elif (item == "FOUR_STAR"):
                    ratingDict[review_text] = 4
                elif (item == "THREE_STAR"):
                    ratingDict[review_text] = 3
                elif (item == "TWO_STAR"):
                    ratingDict[review_text] = 2
                elif (item == "ONE_STAR"):
                    ratingDict[review_text] = 1
        return final_reviews


def filter(reviews):
    '''
    Filters reviews from input json file and returns list of non-fake reviews.
    Uses 'trained_model.pkl' as saved model to run filtering algorithm on. Uses
    'premade_vectorizer.pkl' to vectorize json data. Prints out original size and filtered
    size.

    Args:
        reviews_json (json file): Input json file to filter.

    Returns:
        list: Predicted real reviews.
    '''

    # how to construct the path
    trainedModel_path = os.path.join(
        os.path.dirname(__file__), 'trainedModel.pkl')

    premade_path = os.path.join(
        os.path.dirname(__file__), 'premade.pkl')

    svm_model = joblib.load(trainedModel_path)
    tfidf_vectorizer = joblib.load(premade_path)

    # new_reviews = get_text(reviews_json)
    new_reviews = getReviews(reviews)
    # print(f'Original size: {str(len(new_reviews))}')
    input_reviews_tfidf = tfidf_vectorizer.transform(new_reviews)
    predictions = svm_model.predict(input_reviews_tfidf)
    filtered_reviews = [[]]
    filtered_reviews[0] = [new_reviews[i]
                           for i in range(len(new_reviews)) if predictions[i] == 1]
    # print(f'Final size: {str(len(filtered_reviews[0]))}')
    averageRating = sum([ratingDict[filt]
                        for filt in filtered_reviews[0]]) / len(filtered_reviews[0])
    # print("The new  rating is :")
    # print(averageRating)
    # print("Old Rating is: ")
    # print(sum(ratingDict.values())/len(ratingDict))
    filtered_reviews.append(averageRating)
    return filtered_reviews


def getReviews(data):
    final_reviews = []
    for item in data["data"]:
        for review in data['data'][item]:
            # print(review)
            if (review.get('title', None)):
                if str(review['title']).endswith('.') or str(review['title']).endswith('. '):
                    review_text = review['title'] + ' ' + review['content']
                else:
                    review_text = review['title'] + '. ' + review['content']
            else:
                review_text = '. ' + review['content']
            final_reviews.append(review_text)
            if (item == "FIVE_STAR"):
                # print("It is here!!")
                ratingDict[review_text] = 5
            elif (item == "FOUR_STAR"):
                ratingDict[review_text] = 4
            elif (item == "THREE_STAR"):
                ratingDict[review_text] = 3
            elif (item == "TWO_STAR"):
                ratingDict[review_text] = 2
            elif (item == "ONE_STAR"):
                ratingDict[review_text] = 1

    return final_reviews


def test(json):
    '''
    Testing method to run in file. Runs filter() and prints out the
    filtered reviews, and the execution time.

    Args:
        json (json file): Input json file to test.
    '''

    start_time = time.time()
    filterList = filter(json)

    # print(f'Ran in {time.time() - start_time} seconds')

    return filterList
