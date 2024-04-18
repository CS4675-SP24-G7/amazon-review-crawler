import os
import threading
import time
from flask import Flask, jsonify, request
import selectorlib
import requests
import json
from dateutil import parser as dateparser
from src.url_extractor import *
from src.Shared import Status, Review_Type
import src.firebase as firebase
from src.scraper import to_json, multi_threaded_scrape
from FilterReview.ReviewFilter import *
from geminiAPI import *

app = Flask(__name__)
extractor = selectorlib.Extractor.from_yaml_file('./src/selectors.yml')

# create "temp_data" directory if not exists
if not os.path.exists('temp_data'):
    os.makedirs('temp_data')
if not os.path.exists('data'):
    os.makedirs('data')

Firebase = firebase.Firebase()

@app.route('/')
def index():
    return 'Welcome to Amazon Review Scraper API'


# @app.route('/get_reviews')
# def get_reviews():
#     url = request.args.get('url', None)
#     force = request.args.get('force', False)
#     return api_review(force, url, request.url_root, Firebase)


@app.route('/get_status')
def api_status():
    ISBN = request.args.get('isbn', None)
    if ISBN is None:
        url = request.args.get('url', None)
        if url is None:
            return to_json({'error': 'ISBN or URL not provided'}, 400)
        try:
            ISBN = URL_Processor(url).Extract_ISBN()
        except Exception as e:
            return to_json({'error': str(e)}, 400)

    status = Firebase.Get_Status(ISBN)
    if status is None:
        return to_json({'error': 'ISBN not found'}, 400)
    return to_json(status)


@app.route('/get_data')
def api_data():
    ISBN = request.args.get('isbn', None)
    if ISBN is None:
        url = request.args.get('url', None)
        if url is None:
            return to_json({'error': 'ISBN or URL not provided'}, 400)
        ISBN = URL_Processor(url).Extract_ISBN()

    status = Firebase.Get_Status(ISBN)
    if status == Status.NOT_FOUND.name:
        return to_json({'error': 'ISBN not found'}, 400)
    if status == Status.FAILED.name:
        return to_json({'error': 'Data extraction failed'}, 400)
    if status == Status.PROCESSING.name:
        return to_json({'error': 'Data extraction in progress'}, 400)
    if status == Status.COMPLETED.name:
        try:
            data = Firebase.Get_Review(ISBN)
            return to_json(data)
        except Exception as e:
            return to_json({'error': str(e)}, 400)


@app.route('/scrape')
def scrape_handler():
    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Review(url_processor.Extract_ISBN())

    if status and status['status'] == Status.COMPLETED.name and data:
        theData = filter(data)
        filteredData = "\n".join(theData[0])
        returning = geminiApiCall(filteredData)
        returningData = [[]]
        returningData[0] = returning
        returningData.append(theData[1])
        return jsonify(returningData[0]), 200

    urls = []
    for review_type in Review_Type:
        for i in range(1, 11):
            url_processor = URL_Processor(url, review_type, i)
            url_processor.Extract_ISBN()
            urls.append(url_processor)

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    results = multi_threaded_scrape(urls, Firebase)
    theData = filter(results)
    filteredData = "\n".join(theData[0])
    returning = geminiApiCall(filteredData)
    returningData = [[]]
    returningData[0] = returning
    returningData.append(theData[1])
    return jsonify(returningData[0]), 200

# @app.route('/outputData')
# def outputData():
#     url = request.args.get('url', None)
#     returning = geminiApiCall(url)
#     return returning, 200
    




if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=8080)
