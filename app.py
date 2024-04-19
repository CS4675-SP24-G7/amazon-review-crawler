from flask import Flask, jsonify, request
import selectorlib
from src.url_extractor import *
from src.Shared import Status, Review_Type
import src.firebase as firebase
from src.scraper import to_json, multi_threaded_scrape
from src.FilterReview.ReviewFilter import *
from src.Gemini.geminiAPI import *
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

extractor = selectorlib.Extractor.from_yaml_file('./src/selectors.yml')

Firebase = firebase.Firebase()


@app.route('/')
def index():
    return 'Welcome to Amazon Review Scraper API'


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
    force = request.args.get('force', 'False').lower() == 'true'

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Review(url_processor.Extract_ISBN())

    if not force and status['status'] == Status.COMPLETED.name and data:
        return jsonify(data), 200

    urls = []
    for review_type in Review_Type:
        for i in range(1, 11):
            url_processor = URL_Processor(url, review_type, i)
            url_processor.Extract_ISBN()
            urls.append(url_processor)

    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400

    results = multi_threaded_scrape(urls, Firebase)

    return jsonify(results), 200


@app.route('/filter')
def filter_handler(f=False):
    """
    f is force the scraper to run again
    """

    url = request.args.get('url', None)
    force = request.args.get('force', 'False').lower() == 'true' or f

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Review(url_processor.Extract_ISBN())

    theData = None

    if not force and status['status'] == Status.COMPLETED.name and data:
        if 'filtered' in data:
            theData = data['filtered']
            return jsonify(theData), 200

    else:
        scrape_handler()
        data = Firebase.Get_Review(url_processor.Extract_ISBN())

    theData = filter(data)[0]
    Firebase.Set_Filters(url_processor.Extract_ISBN(), theData)

    return jsonify(theData), 200


@app.route('/summary')
def summary_handler():

    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Filters(url_processor.Extract_ISBN())

    theData = None

    if status['status'] == Status.COMPLETED.name and data:
        theData = data
    else:
        filter_handler(f=True)
        data = Firebase.Get_Filters(url_processor.Extract_ISBN())
        theData = data

    filteredData_str = "\n".join(theData)

    summary = gemini_summary(filteredData_str)
    summary_json = gemini_extract_json(summary)

    return jsonify(summary_json), 200


@app.route('/ad')
def ad_handler():

    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Filters(url_processor.Extract_ISBN())

    theData = None

    if status['status'] == Status.COMPLETED.name and data:
        theData = data
    else:
        filter_handler(f=True)
        data = Firebase.Get_Filters(url_processor.Extract_ISBN())
        theData = data

    filteredData_str = "\n".join(theData)

    summary = gemini_a_d(filteredData_str)
    summary_json = gemini_extract_json(summary)

    return jsonify(summary_json), 200


if __name__ == '__main__':
    # remove all _pycache_ folders
    import os
    import shutil
    for root, dirs, files in os.walk(".", topdown=False):
        for name in dirs:
            if name == "__pycache__":
                shutil.rmtree(os.path.join(root, name))

    app.debug = True
    app.run(host="0.0.0.0", port=8080)
