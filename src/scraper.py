from ssl import Options
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
# fake user agents
from fake_useragent import UserAgent
# import beautifulsoup
from bs4 import BeautifulSoup
# import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import threading


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


def to_json(data, status=200):
    return json.dumps(data, indent=2), status, {'Content-Type': 'application/json; charset=utf-8'}


def init_driver():
    chrome_options = webdriver.ChromeOptions()

    # Set the custom User-Agent
    my_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
    chrome_options.add_argument(f"--user-agent={my_user_agent}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # disable javascript
    chrome_options.add_argument("--disable-javascript")

    driver = webdriver.Chrome(options=chrome_options)

    return driver


def multi_threaded_scrape(urls, Firebase: firebase.Firebase):

    driver = init_driver()

    composed_url = urls[0].Compose_Review_URL()
    original_url = f"{composed_url}/"

    driver.get("https://amazon.com")
    driver.implicitly_wait(10)

    TEMP = {
        "ibsn": urls[0].IBSN,
        "last_update": "",
        "time_taken": 0,
        "product_title": "",
        "product_url": original_url.replace("/product-reviews/", "/dp/"),
        "original_rating": -1,
        "data": {
            Review_Type.ONE_STAR.name: [],
            Review_Type.TWO_STAR.name: [],
            Review_Type.THREE_STAR.name: [],
            Review_Type.FOUR_STAR.name: [],
            Review_Type.FIVE_STAR.name: []
        }
    }
    start_time = time.time()

    jobs = []

    th = threading.Thread(target=first_page_scrape, args=(
        init_driver(), composed_url, TEMP))
    jobs.append(th)
    th.start()

    for review_type in Review_Type:
        composed_url = f"{original_url}?filterByStar={review_type.name.lower()}"
        th = threading.Thread(target=single_scrape, args=(
            init_driver(), composed_url, TEMP))
        jobs.append(th)
        th.start()

    for job in jobs:
        job.join()

    TEMP['time_taken'] = time.time() - start_time
    TEMP['last_update'] = str(dateparser.parse(time.ctime()))

    # remove duplicated reviews each star
    for review_type in Review_Type:
        TEMP['data'][review_type.name] = list(
            {v['content']: v for v in TEMP['data'][review_type.name]}.values())

    Firebase.Insert(f"{Status.COMPLETED.name}/{TEMP['ibsn']}", TEMP)
    Firebase.Set_Status(TEMP['ibsn'], Status.COMPLETED, {
        "last_update": str(dateparser.parse(time.ctime())),
        "time_taken": TEMP["time_taken"],
        Review_Type.ONE_STAR.name: len(TEMP['data'][Review_Type.ONE_STAR.name]),
        Review_Type.TWO_STAR.name: len(TEMP['data'][Review_Type.TWO_STAR.name]),
        Review_Type.THREE_STAR.name: len(TEMP['data'][Review_Type.THREE_STAR.name]),
        Review_Type.FOUR_STAR.name: len(TEMP['data'][Review_Type.FOUR_STAR.name]),
        Review_Type.FIVE_STAR.name: len(TEMP['data'][Review_Type.FIVE_STAR.name]),
    })

    return TEMP


def first_page_scrape(driver, composed_url, TEMP):
    while True:
        driver.get(composed_url)

        if TEMP['product_title'] == "":
            TEMP['product_title'] = driver.find_element(
                By.XPATH,
                '//*[@data-hook="product-link"]').get_attribute('innerHTML')

        if TEMP['original_rating'] == -1:
            TEMP['original_rating'] = float(driver.find_element(
                By.XPATH,
                '//*[@data-hook="average-star-rating"]/span').get_attribute('innerHTML').split(' ')[0])

        stars = driver.find_elements(
            By.XPATH,
            '//*[@data-hook="review"]/div/div/div[2]/a/i/span')

        contents = driver.find_elements(
            By.XPATH,
            '//*[@data-hook="review"]/div/div/div[4]/span/span')

        for i in range(min(len(stars), len(contents))):
            starInt = int(
                float(stars[i].get_attribute('innerHTML').split(' ')[0]))

            starMap: Review_Type = None

            if starInt == 1:
                starMap = Review_Type.ONE_STAR.name
            elif starInt == 2:
                starMap = Review_Type.TWO_STAR.name
            elif starInt == 3:
                starMap = Review_Type.THREE_STAR.name
            elif starInt == 4:
                starMap = Review_Type.FOUR_STAR.name
            elif starInt == 5:
                starMap = Review_Type.FIVE_STAR.name

            TEMP['data'][starMap].append({
                'content': contents[i].get_attribute('innerHTML'),
                'rating': starInt
            })

        # for star in stars:
        #     print(star.get_attribute('innerHTML'))

        # perform click on button xpath //*[@id="cm_cr-pagination_bar"]/ul/li[2]
        next_page = driver.find_element(
            By.XPATH,
            '//*[@id="cm_cr-pagination_bar"]/ul/li[2]')

        # check if the next page is disabled
        if 'a-disabled' in next_page.get_attribute('class'):
            break

        next_page = driver.find_element(
            By.XPATH,
            '//*[@id="cm_cr-pagination_bar"]/ul/li[2]/a')

        # extract href attribute
        composed_url = next_page.get_attribute('href')


def single_scrape(driver, composed_url, TEMP):
    while True:
        driver.get(composed_url)

        stars = driver.find_elements(
            By.XPATH,
            '//*[@data-hook="review"]/div/div/div[2]/a/i/span')

        contents = driver.find_elements(
            By.XPATH,
            '//*[@data-hook="review"]/div/div/div[4]/span/span')

        for i in range(min(len(stars), len(contents))):
            starInt = int(
                float(stars[i].get_attribute('innerHTML').split(' ')[0]))

            starMap: Review_Type = None

            if starInt == 1:
                starMap = Review_Type.ONE_STAR.name
            elif starInt == 2:
                starMap = Review_Type.TWO_STAR.name
            elif starInt == 3:
                starMap = Review_Type.THREE_STAR.name
            elif starInt == 4:
                starMap = Review_Type.FOUR_STAR.name
            elif starInt == 5:
                starMap = Review_Type.FIVE_STAR.name

            TEMP['data'][starMap].append({
                'content': contents[i].get_attribute('innerHTML'),
                'rating': starInt
            })

        # for star in stars:
        #     print(star.get_attribute('innerHTML'))

        # perform click on button xpath //*[@id="cm_cr-pagination_bar"]/ul/li[2]
        next_page = driver.find_element(
            By.XPATH,
            '//*[@id="cm_cr-pagination_bar"]/ul/li[2]')

        # check if the next page is disabled
        if 'a-disabled' in next_page.get_attribute('class'):
            break

        next_page = driver.find_element(
            By.XPATH,
            '//*[@id="cm_cr-pagination_bar"]/ul/li[2]/a')

        # extract href attribute
        composed_url = next_page.get_attribute('href')
