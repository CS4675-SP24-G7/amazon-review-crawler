import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import json
import threading

SELENIUM_BASEURL = "http://172.17.0.1:4444/wd/hub"


def init_driver():
    options = webdriver.ChromeOptions()

    # Set the custom User-Agent
    my_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
    options.add_argument(f"--user-agent={my_user_agent}")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    # disable javascript
    options.add_argument("--disable-javascript")

    driver = webdriver.Chrome(options=options)

    # driver = webdriver.Remote(
    #     command_executor=SELENIUM_BASEURL,
    #     options=options
    # )

    return driver


def get_comments(product_name="echo dot 3rd gen"):

    start_time = time.time()

    product_name = product_name.replace(" ", "+")

    driver = init_driver()

    driver.get(
        f"https://www.google.com/search?q=site%3Areddit.com+{product_name}")

    links = driver.find_elements(
        By.XPATH, '//div[@class="yuRUbf"]//a')

    hrefs = [link.get_attribute("href") for link in links]

    all_comments = []

    # get only top <= 10 links
    if len(hrefs) > 10:
        hrefs = hrefs[:10]

    jobs = []

    # open each link and get the comments
    for i, href in enumerate(hrefs):

        th = threading.Thread(target=single_scrape, args=(href, all_comments))
        jobs.append(th)
        th.start()

    for job in jobs:
        job.join()

    driver.quit()

    return {
        "comments": all_comments,
        "number_of_comments": len(all_comments),
        "time": time.time() - start_time,
    }


def single_scrape(url, ALL_COMMENTS):
    driver = init_driver()

    driver.get(url)

    prev_height = -1
    max_scrolls = 100
    scroll_count = 0

    while scroll_count < max_scrolls:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # give some time for new results to load
        new_height = driver.execute_script(
            "return document.body.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height
        scroll_count += 1

        btn = driver.find_elements(
            By.XPATH, '//*[@id="comment-tree"]/faceplate-partial/div[1]/button')
        if len(btn) > 0:
            btn[0].click()

    driver.set_page_load_timeout(5)

    comments = driver.find_elements(
        By.XPATH, '//shreddit-comment[@depth=0]/div[3]')

    for comment in comments:
        if comment.text.strip() != "":
            ALL_COMMENTS.append(comment.text)

    driver.quit()
