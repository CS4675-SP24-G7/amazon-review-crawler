import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"

options = webdriver.ChromeOptions()
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-running-insecure-content')
options.add_argument("--disable-extensions")
options.add_argument("--proxy-server='direct://'")
options.add_argument("--proxy-bypass-list=*")
options.add_argument("--start-maximized")
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
# options.add_argument('--headless')

driver = webdriver.Remote(
    command_executor='http://127.0.0.1:4444/wd/hub',
    options=options
)


def get_comments(product_name="echo dot 3rd gen"):

    product_name = product_name.replace(" ", "+")

    driver.get(
        f"https://www.google.com/search?q=site%3Areddit.com+{product_name}")

    links = driver.find_elements(
        By.XPATH, '//*[@id="rso"]/div[*]/div/div/div[1]/div/div/span/a')

    hrefs = [link.get_attribute("href") for link in links]

    all_comments = []

    # get only top <= 10 links
    if len(hrefs) > 10:
        hrefs = hrefs[:10]

    # open each link and get the comments
    for i, href in enumerate(hrefs):
        # process each href
        driver.get(href)

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

        driver.set_page_load_timeout(10)

        comments = driver.find_elements(
            By.XPATH, '//shreddit-comment[@depth=0]/div[3]')

        for comment in comments:
            print(comment.text)
            all_comments.append(comment.text)

    return all_comments


get_comments("samsung galaxy s24 ultra")
