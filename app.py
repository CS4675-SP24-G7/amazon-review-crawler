import time
from flask import Flask, request
import selectorlib
import requests
import json
from dateutil import parser as dateparser
from url_extractor import *
from fake_useragent import UserAgent
from utils import Join_JSON
from db_adapter import *

app = Flask(__name__)
extractor = selectorlib.Extractor.from_yaml_file('selectors.yml')


def scrape(url, user_agent):
    headers = {
        'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        # 'user-agent': user_agent,
        # 'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests
    print("Downloading %s" % url)
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            raise Exception(
                "Page %s was blocked by Amazon. Please try using better proxies\n" % url)
        else:
            raise Exception("Page %s must have been blocked by Amazon as the status code was %d" % (
                url, r.status_code))

    # Pass the HTML of the page and create
    data = extractor.extract(r.text, base_url=url)

    # check if the extracted data is empty
    if data['reviews'] is None:
        raise Exception("ERROR: No data extracted. Check selector config")

    reviews = []
    for r in data['reviews']:
        r['rating'] = int(float(r['title'].split(' out of')[0]))
        r['title'] = r['title'].split(' out of 5 stars ')[-1]
        r['product'] = data['product_title']
        r['url'] = url
        if r['found_helpful'] is None:
            r['found_helpful'] = 0
        elif 'One person found this helpful' in r['found_helpful']:
            r['found_helpful'] = 1
        elif 'people found this helpful' in r['found_helpful']:
            r['found_helpful'] = int(r['found_helpful'].split()[0])
        else:
            r['found_helpful'] = 0
        if 'verified_purchase' in r and r['verified_purchase'] is not None:
            if 'Verified Purchase' in r['verified_purchase']:
                r['verified_purchase'] = True
            else:
                r['verified_purchase'] = False
        date_posted = r['date'].split('on ')[-1]
        if r['images']:
            r['images'] = "\n".join(r['images'])
        r['date'] = dateparser.parse(date_posted).strftime('%d %b %Y')
        reviews.append(r)
    data['reviews'] = reviews
    histogram = {}
    for h in data['histogram']:
        histogram[h['key']] = h['value']
    data['histogram'] = histogram
    data['average_rating'] = float(data['average_rating'].split(' out')[0])
    data['number_of_reviews'] = int(data['number_of_reviews'].split(
        ' global ratings')[0].replace(',', ''))
    return data


def to_json(data, status=200):
    return json.dumps(data, indent=2), status, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/')
def index():
    return 'Welcome to Amazon Review Scraper API'


@app.route('/get_reviews')
def api_review():
    # set up timer
    start = time.time()

    url = request.args.get('url', None)
    ISBN = URL_Processor(url, Review_Type.ONE_STAR, 0).Extract_ISBN()

    Insert_Status(ISBN, Status.PROCESSING, str(
        start), '', '', '', '', '', '', '')

    user_agent = UserAgent().random

    for review_type in Review_Type:
        for i in range(1, 11):
            url_processor = URL_Processor(url, review_type, i)
            try:
                ISBN = url_processor.Extract_ISBN()
                review_url = url_processor.Compose_Review_URL()
                data = api(review_url, user_agent)

                # check if json has error key
                if 'error' in json.loads(data[0]):
                    continue
                else:
                    # write data to file
                    with open(f'./temp_data/{url_processor.IBSN}_{review_type.name}_{i}.json', 'w') as f:
                        f.write(data[0])
                        f.close()

            except Exception as e:
                return to_json({'error': str(e)}, 400)

    # join all json files
    Join_JSON(ISBN)

    # end timer
    end = time.time()

    Insert_Status(ISBN, Status.COMPLETED, str(end),
                  f'{end - start:.2f} seconds', '', '', '', '', '', '')

    return Get_Stats(ISBN)


@app.route('/get_status')
def api_status():
    ISBN = request.args.get('isbn', None)
    status = Get_Status(ISBN)
    if status == Status.NOT_FOUND.name:
        return to_json({'error': 'ISBN not found'}, 400)
    return to_json({
        'isbn': ISBN,
        'status': status,
    })


@app.route('/get_stats')
def api_stats():
    ISBN = request.args.get('isbn', None)
    status = Get_Status(ISBN)
    if status == Status.NOT_FOUND.name:
        return to_json({'error': 'ISBN not found'}, 400)
    if status == Status.FAILED.name:
        return to_json({'error': 'Data extraction failed'}, 400)
    if status == Status.PROCESSING.name:
        return to_json({'error': 'Data extraction in progress'}, 400)
    if status == Status.COMPLETED.name:
        stats = Get_Stats(ISBN)
        return to_json(stats)


@app.route('/get_data')
def api_data():
    ISBN = request.args.get('isbn', None)
    status = Get_Status(ISBN)
    if status == Status.NOT_FOUND.name:
        return to_json({'error': 'ISBN not found'}, 400)
    if status == Status.FAILED.name:
        return to_json({'error': 'Data extraction failed'}, 400)
    if status == Status.PROCESSING.name:
        return to_json({'error': 'Data extraction in progress'}, 400)
    if status == Status.COMPLETED.name:
        try:
            with open(f'./data/{ISBN}.json', 'r') as f:
                data = json.load(f)
                f.close()
            return to_json(data)
        except Exception as e:
            return to_json({'error': str(e)}, 400)


def api(url, user_agent):
    if request.args.get('pageNumber', None) is None:
        url += '&pageNumber=1'
    elif int(request.args.get('pageNumber', None)) <= 10:
        url += '&pageNumber=' + request.args.get('pageNumber', None)
    else:
        return to_json({'error': 'Page number should be less than or equal to 10'}, 400)

    if url:
        try:
            data = scrape(url, user_agent)
            return to_json(data)
        except Exception as e:
            return to_json({'error': str(e)}, 400)
    return to_json({'error': 'URL to scrape is not provided'}, 400)


if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
