import time
import selectorlib
import requests
import json
from dateutil import parser as dateparser
from src.url_extractor import *
from src.Shared import Status, Review_Type
import src.firebase as firebase
import threading
import random

extractor = selectorlib.Extractor.from_yaml_file('./src/selectors.yml')

user_agent_list = [
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3", "pct": 32.54},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.1", "pct": 20.51},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.", "pct": 14.24},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.3", "pct": 10.17},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3", "pct": 6.78},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.1", "pct": 5.42},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.1", "pct": 4.92},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3", "pct": 2.71},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.", "pct": 1.36},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.", "pct": 0.68},
    {"ua": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.", "pct": 0.68}
]


def scrape(url):
    headers = {
        'authority': 'www.amazon.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': random.choices(user_agent_list)[0]['ua'],
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # load cookies.json from /cred folder
    with open('cred/cookies.json') as f:
        cookies = json.load(f)

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


def scrape_thread(url_processor: URL_Processor, temp_data, Firebase: firebase.Firebase):
    data = scrape(url_processor.Compose_Review_URL())
    if data is None:
        return

    Firebase.Set_Status(url_processor.IBSN, Status.PROCESSING, None)

    temp_data['ibsn'] = url_processor.IBSN
    temp_data['product_title'] = data['product_title']
    temp_data['product_url'] = f"https://www.amazon.com/dp/{url_processor.IBSN}"
    temp_data['data'][url_processor.Review_Type.name] += data['reviews']

    # temp_data.append(data)


def multi_threaded_scrape(urls, Firebase: firebase.Firebase):
    start_time = time.time()
    threads = []

    TEMP_DATA = {
        "ibsn": "",
        "last_update": "",
        "time_taken": 0,
        "product_title": "",
        "product_url": "",
        "data": {
                Review_Type.ONE_STAR.name: [],
                Review_Type.TWO_STAR.name: [],
                Review_Type.THREE_STAR.name: [],
                Review_Type.FOUR_STAR.name: [],
                Review_Type.FIVE_STAR.name: []
        }
    }

    for url_processor in urls:
        thread = threading.Thread(
            target=scrape_thread, args=(url_processor, TEMP_DATA, Firebase))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    TEMP_DATA['time_taken'] = time.time() - start_time
    TEMP_DATA['last_update'] = str(dateparser.parse(time.ctime()))

    Firebase.Insert(f"{Status.COMPLETED.name}/{TEMP_DATA['ibsn']}", TEMP_DATA)
    Firebase.Set_Status(url_processor.IBSN, Status.COMPLETED, {
        "last_update": str(dateparser.parse(time.ctime())),
        "time_taken": TEMP_DATA["time_taken"],
        Review_Type.ONE_STAR.name: len(TEMP_DATA['data'][Review_Type.ONE_STAR.name]),
        Review_Type.TWO_STAR.name: len(TEMP_DATA['data'][Review_Type.TWO_STAR.name]),
        Review_Type.THREE_STAR.name: len(TEMP_DATA['data'][Review_Type.THREE_STAR.name]),
        Review_Type.FOUR_STAR.name: len(TEMP_DATA['data'][Review_Type.FOUR_STAR.name]),
        Review_Type.FIVE_STAR.name: len(TEMP_DATA['data'][Review_Type.FIVE_STAR.name]),
    })

    return TEMP_DATA
