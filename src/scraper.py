import os
import time
from flask import Flask, request
import selectorlib
import requests
import json
from dateutil import parser as dateparser
from src.url_extractor import *
from src.Shared import Status, Review_Type
import src.firebase as firebase

app = Flask(__name__)
extractor = selectorlib.Extractor.from_yaml_file('./src/selectors.yml')

Firebase = None


def scrape(url):
    headers = {
        'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests

    cookies = {
        
    }

    r = requests.get(url, headers=headers, cookies=cookies)
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
        return
        # return to_json({'error': 'No data extracted. Check selector config'}, 400)
    #     raise Exception("ERROR: No data extracted. Check selector config")

    reviews = []
    for r in data['reviews']:
        if r['title']:
            r['rating'] = int(float(r['title'][:3]))
            r['title'] = r['title'][18:].strip()
        r['product'] = data['product_title']
        r['url'] = url
        if r['found_helpful'] is None:
            r['found_helpful'] = 0
        elif 'One person found this helpful' in r['found_helpful']:
            r['found_helpful'] = 1
        elif 'people found this helpful' in r['found_helpful']:
            r['found_helpful'] = int(
                str(r['found_helpful']).replace(',', '').split()[0])
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


def api_review(force, url, url_root, firebase):
    global Firebase
    Firebase = firebase

    # set up timer
    start = time.time()

    TEMP_DATA = {
        "ibsn": "",
        "last_update": "",
        "time_taken": 0,
        "product_title": "",
        "product_url": "",
        "review_url": "",
        "data": {
                Review_Type.ONE_STAR.name: [],
                Review_Type.TWO_STAR.name: [],
                Review_Type.THREE_STAR.name: [],
                Review_Type.FOUR_STAR.name: [],
                Review_Type.FIVE_STAR.name: []
        }
    }

    for review_type in Review_Type:
        for i in range(1, 11):
            url_processor = URL_Processor(url, review_type, i)
            try:
                ISBN = url_processor.Extract_ISBN()

                if force is False and Firebase.Get_Status(ISBN)['status'] == Status.COMPLETED.name:
                    return Firebase.Get_Review(ISBN)

                if TEMP_DATA['ibsn'] == "":
                    TEMP_DATA['ibsn'] = ISBN
                    Firebase.Remove_Review(ISBN)
                    Firebase.Remove_Status(ISBN)
                    Firebase.Set_Status(
                        ISBN,
                        Status.PROCESSING,
                        {"start_time": str(start)})
                if TEMP_DATA['product_url'] == "":
                    TEMP_DATA['product_url'] = f"https://www.amazon.com/dp/{ISBN}"
                if TEMP_DATA['review_url'] == "":
                    TEMP_DATA['review_url'] = f"{url_root}get_data?isbn={ISBN}"

                product_review_url = url_processor.Compose_Review_URL()
                data = decider(product_review_url)

                # check if json has error key
                if 'error' in json.loads(data[0]):
                    continue
                else:
                    data = json.loads(data[0])

                    if TEMP_DATA['product_title'] == "":
                        TEMP_DATA['product_title'] = data['product_title']
                        Firebase.Set_Status(
                            ISBN,
                            None,
                            {"product_title": data['product_title']}
                        )

                    TEMP_DATA['data'][review_type.name] += data['reviews']

            except Exception as e:
                return to_json({'error': str(e)}, 400)

    # end timer
    end = time.time()

    if TEMP_DATA["time_taken"] == 0:
        TEMP_DATA["time_taken"] = f'{end - start:.2f} seconds'

    if TEMP_DATA["last_update"] == "":
        TEMP_DATA["last_update"] = str(end)

    Firebase.Insert(f"{Status.COMPLETED.name}/{TEMP_DATA['ibsn']}", TEMP_DATA)
    Firebase.Set_Status(
        TEMP_DATA['ibsn'],
        Status.COMPLETED,
        {"last_update": str(end),
         "time_taken": TEMP_DATA["time_taken"],
         Review_Type.ONE_STAR.name: len(TEMP_DATA['data'][Review_Type.ONE_STAR.name]),
         Review_Type.TWO_STAR.name: len(TEMP_DATA['data'][Review_Type.TWO_STAR.name]),
         Review_Type.THREE_STAR.name: len(TEMP_DATA['data'][Review_Type.THREE_STAR.name]),
         Review_Type.FOUR_STAR.name: len(TEMP_DATA['data'][Review_Type.FOUR_STAR.name]),
         Review_Type.FIVE_STAR.name: len(TEMP_DATA['data'][Review_Type.FIVE_STAR.name]), }
    )

    # return Firebase.Get_Status(ISBN)
    return Firebase.Get_Review(ISBN)


def decider(url):
    if request.args.get('pageNumber', None) is not None and int(request.args.get('pageNumber', None)) > 10:
        return to_json({'error': 'Page number should be less than or equal to 10'}, 400)

    if url:
        try:
            data = scrape(url)
            return to_json(data)
        except Exception as e:
            return to_json({'error': str(e)}, 400)
    return to_json({'error': 'URL to scrape is not provided'}, 400)
