from flask import Flask, jsonify, request
import selectorlib
from src.url_extractor import *
from src.Shared import Status, Review_Type
import src.firebase as firebase
from src.scraper import to_json, multi_threaded_scrape
from src.FilterReview.ReviewFilter import *
from src.Gemini.geminiAPI import *
from src.reddit import runner as reddit
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

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


@app.route('/reddit')
def reddit_handler():
    url = request.args.get('url', None)
    force = request.args.get('force', 'False').lower() == 'true'

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Review(url_processor.Extract_ISBN())

    if not force and status['status'] == Status.COMPLETED.name and data:
        if 'reddit' in data and data['reddit'] != '':
            return jsonify(data['reddit']), 200
        else:
            result = reddit.get_comments(data['product_title'])
            Firebase.Insert(
                f"{Status.COMPLETED.name}/{url_processor.Extract_ISBN()}/reddit", result)
            return jsonify(result), 200

    scrape_handler()
    data = Firebase.Get_Review(url_processor.Extract_ISBN())
    result = reddit.get_comments(data['product_title'])
    Firebase.Insert(
        f"{Status.COMPLETED.name}/{url_processor.Extract_ISBN()}/reddit", result)

    return jsonify(result), 200


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

    if not force and status['status'] == Status.COMPLETED.name \
            and 'filtered' in data and data['filtered']:
        theData = data['filtered']
        return jsonify(theData), 200

    else:
        scrape_handler()
        data = Firebase.Get_Review(url_processor.Extract_ISBN())

    if not data:
        return jsonify({'error': 'No data found'}), 400

    theData = filter(data)[0]
    Firebase.Set_Filters(url_processor.Extract_ISBN(), theData)

    return jsonify(theData), 200


@app.route('/product_details')
def product_details_handler():
    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Product_Details(url_processor.IBSN)

    if not data:
        return jsonify({'error': 'No data found'}), 400

    print(data)
    return jsonify([data]), 200


@app.route('/summary')
def summary_handler():

    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Filters(url_processor.Extract_ISBN())

    theData = None

    if status['status'] == Status.COMPLETED.name and data:
        print('Go here 1')
        theData = data
    else:
        print('Go here 2')

        filter_handler(f=True)
        data = Firebase.Get_Filters(url_processor.Extract_ISBN())
        theData = data

    if theData == None:
        return jsonify([{'summary': 'No data found. Please try other products.', 'rating': 'N/A'}]), 200

    filteredData_str = "\n".join(theData)

    summary = gemini_summary(filteredData_str, Firebase)
    summary_json = gemini_extract_json(summary)

    return jsonify(summary_json), 200


@app.route('/reddit_summary')
def reddit_summary_handler():

    url = request.args.get('url', None)

    url_processor = URL_Processor(url, Review_Type.FIVE_STAR, 0)
    status = Firebase.Get_Status(url_processor.Extract_ISBN())
    data = Firebase.Get_Reddit(url_processor.Extract_ISBN())

    theData = None

    try:
        if status['status'] == Status.COMPLETED.name and data:
            theData = data
        else:
            reddit_handler()
            theData = Firebase.Get_Reddit(url_processor.Extract_ISBN())

        if (theData is None or theData['number_of_comments'] == 0):
            return jsonify([{'summary': 'No data found on Reddit. Please try other products.', 'rating': 'N/A'}]), 200

        filteredData_str = "\n".join(theData['comments'])

        summary = gemini_summary(filteredData_str, Firebase)
        summary_json = gemini_extract_json(summary)

        print(summary_json)

        return jsonify(summary_json), 200
    except Exception as e:
        return jsonify([{'summary': 'No data found on Reddit. Please try other products.', 'rating': 'N/A'}]), 200


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

    summary = gemini_a_d(filteredData_str, Firebase)
    summary_json = gemini_extract_json(summary)

    return jsonify(summary_json), 200


@app.route('/decision')
def decision_handler():

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

    summary = gemini_decision(filteredData_str, Firebase)
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
