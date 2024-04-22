import requests
import re
import time
import json
import multiprocessing
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
# from openai import OpenAI


# # OpenAI relevance evaluation
# client = OpenAI()

def evaluate_relevance(comment, shortened):
    response = client.chat.completions.create(model="gpt-3.5-turbo-0125", messages=[
        {"role": "user",
         "content": "Respond with 'Y' for yes or 'N' for no: whether the following comment provides a relevant opinion about the specific product, " + shortened + ", that other buyers may want to hear. \n\nComment: " + comment, }
    ])
    output = response.choices[0].message.content.strip().lower()[0]
    if output == 'y':
        # print("Relevant comment: " + comment)
        return True
    elif output == 'n':
        # print("Irrelevant comment: " + comment)
        return False
    else:
        # print("Unknown output: " + output + "\nWill be returned as relevant")
        return True


# Reddit post parsing logic
def parse(url_id, driver, assist_queue, r, shortened):
    url, id = url_id
    clean_url = re.sub(r'&sa.*', '', url)

    # print(f'Session {url_id}: Starting parsing of '+clean_url)

    # Obtaining the post HTML
    driver.get(clean_url)
    driver.implicitly_wait(0.1)
    reddit_response = driver.page_source

    # Soup parsing
    soup = BeautifulSoup(reddit_response, 'html.parser')

    # Setting post information
    post_title = soup.find('h1', {'id': re.compile(r'^post-title-t3_.*$')})
    post_title = post_title.get_text().strip() if post_title else None
    author = soup.find('shreddit-post-overflow-menu',
                       {'author-name': re.compile(r'^.+$')})
    author = author.get('author-name', None) if author else None
    if not post_title or not author:
        print(f'Post or author not found at URL: {clean_url}')
        return
    post_content = soup.find(
        'div', {'id': re.compile(r'^t3_.+-post-rtjson-content$')})
    post_content = post_content.get_text().strip() if post_content else None

    # Forming comment dictionary
    comment_elems = soup.find_all(
        'shreddit-comment', {'author': re.compile(r"^.+$")})
    commenters = []
    comments = {}
    if comment_elems:
        for tag in comment_elems:
            if tag['author'] == "[deleted]":
                continue
            content = soup.find(
                'div', {'id': tag['thingid']+"-comment-rtjson-content"}).get_text().strip()
            if content and evaluate_relevance(content, shortened) == False:
                continue
            comments[tag['author']] = {
                "Comment ID": tag['thingid'],
                "Parent ID": tag.get('parentid', None),
                "Content": content,
                "Score": tag['score'],
            }

    post_opinion = post_title + post_content if post_content else post_title

    post_details = {
        'Link': clean_url,
        'Title': post_title,
        'Content': post_content,
        'Opinion': evaluate_relevance(post_opinion, shortened),
        'Author': author,
        'Comments': comments,
        'Authenticity Metrics': {},
    }

    r[id] = json.dumps(post_details)  # Set the dictionary in manager array

    users = list(set(commenters))
    users.append(author)

    # Gathering authenticity metrics
    for user in users:
        assist_queue.put((user, id))

    # Keep waiting for remaining user URLs to parse
    while True:
        try:
            user = assist_queue.get(block=False)[0]
            parse_user(user, driver, r, id)
        except multiprocessing.queues.Empty:
            break

    # print(f'URL {id} finished parsing')


# Parsing logic for gathering authenticity metrics
def parse_user(user, driver, r, id):
    # Get URL string
    user_url = "https://reddit.com/user/"+user+"/"
    # print("Getting authenticity from user URL: "+user_url)

    # Driver actions
    driver.get(user_url)
    driver.implicitly_wait(0.1)
    html = driver.page_source

    # Scrape and add to result string
    soup = BeautifulSoup(html, 'html.parser')
    moderating = soup.find('h2', text=re.compile(r'^.*Moderator.*$'))
    moderating = len(
        moderating.find_next_sibling().contents) if moderating else None

    if soup.find('shreddit-forbidden', {'reason': '"BANNED"'}):
        return None
    metrics = {
        "Total Karma": sum([int(tag.get_text().strip().replace(",", "")) for tag in soup.find_all('span', {'data-testid': 'karma-number'})]),
        "Cake Day": soup.find('time', {'data-testid': 'cake-day'})['datetime'],
        "Bio": True if soup.find('p', {'data-testid': 'profile-description'}) else False,
        "Communities Moderating": moderating,
        "Trophy Count": len(soup.find('ul', {'slot': 'initial-trophies'}).contents),
    }

    # Placing into shared memory string
    pattern = r'"Authenticity Metrics": (\{.*?\})'
    authenticity_metrics = json.loads(
        re.search(pattern, r[id], re.DOTALL).group(1))
    authenticity_metrics[user] = metrics
    updated_metrics = json.dumps(authenticity_metrics)
    r[id] = re.sub(
        pattern, f'"Authenticity Metrics": {updated_metrics}', r[id], flags=re.DOTALL)


def session(url_queue, assist_queue, r, shortened):
    # Configure a remote WebDriver
    options = webdriver.ChromeOptions()
    # TODO: fake user agent string
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=options
    )

    # Logic for prioritizing queues
    while True:
        try:
            user, id = assist_queue.get(block=False)
            parse_user(user, driver, r, id)
        except multiprocessing.queues.Empty:
            url_id = url_queue.get()
            if url_id is None:
                driver.quit()
                break
            parse(url_id, driver, assist_queue, r, shortened)


def run_parallel_parsing(urls, processes, shortened):
    url_queue = multiprocessing.Queue()
    assist_queue = multiprocessing.Queue()

    # Initializing process queue, assist list, and session processes
    r = multiprocessing.Manager().list([""]*len(urls))
    for id in range(len(urls)):
        url_queue.put((urls[id], id))
    sessions = []
    for _ in range(processes):
        # Start driver process
        process = multiprocessing.Process(
            target=session, args=(url_queue, assist_queue, r, shortened))
        process.start()
        sessions.append(process)

    # Signals for the sessions to stop
    for _ in range(processes):
        url_queue.put(None)

    # Wait for all processes to finish
    for s in sessions:
        s.join()

    results = list(r)

    # Write the final output
    with open('output.json', 'w') as file:
        parsed_results = [json.loads(result) for result in results]
        json.dump(parsed_results, file, indent=2)


if __name__ == '__main__':
    start = time.time()

    # TODO: Interface the product name with an LLM for a shortened search term for Google
    # product_name = get_product_data()
    # print(f"Product Name: {product_name}")

    shortened = '"nike reax"'
    shortened = shortened.replace(" ", "+")

    # Forming Google Dorks queries
    search_query = "site%3Areddit.com+" + shortened
    url = f"https://www.google.com/search?q={search_query}"
    r = requests.get(url)

    # Gathering URLs from the search
    soup = BeautifulSoup(r.text, "html.parser")
    reddit_urls = []
    for link in soup.select("div.egMi0.kCrYT a"):
        reddit_urls.append(link["href"].replace('/url?q=', ''))

    # Multiprocessing
    processes = 6
    run_parallel_parsing(reddit_urls, processes, shortened)

    # Final touches
    end = time.time()
    print(f"Execution time: {end - start} seconds")
