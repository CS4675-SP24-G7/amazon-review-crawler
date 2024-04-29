
import os
import random
import re
import json

JSON_MODEL_A_D = """
Provide a response in a structured JSON format that matches the following model:
{"advantages": ["advantage 1", "advantage 2", "advantage 2", ...],
"disadvantages": ["disadvantage 1", "disadvantage 2", "disadvantage 3", ...]}
"""

JSON_MODEL_SUMMARY = """
Provide a response in a structured JSON format that matches the following model:
{"summary": "",
"rating": 0.0}
"""

JSON_MODEL_DECISION = """
Provide a response in a structured JSON format that matches the following model:
{"buying_decision": true/false},
"reason": ""}
Where buying_decision is a boolean (true means should buy, false means should not buy) 
and reason is a string, explains why buying_decision is made.
"""

GENERATE_SUMMARY = """
Make a summary from the provided reviews data. 
Condition 1: Give me a summary of no more than 10 sentences.
Condition 2: Using the original given Amazon Rating with the filtered review data. 
On a scale of 0 to 5, give me the average rating of the reviews. 
Where 0 is the worst and 5 is the best.
Condition 3: No markdown, no HTML, no special characters.
Only use the provided resources.
"""

GENERATE_REDDIT_SUMMARY = """
Make a summary from the provided reviews data. Only evaluate if the data is rellated to the product. Otherwise, return the base json model.
Condition 1: Give me a summary of no more than 10 sentences. 
Condition 2: Using the original given Amazon Rating with the Reddit review data. 
On a scale of 0 to 5, give me the average rating of the reviews. 
Where 0 is the worst and 5 is the best.
Condition 3: No markdown, no HTML, no special characters.
Only use the provided resources.
"""

GENERATE_A_D = """
Make me Advantage, and Disadvantage from the provided reviews data. 
Condition 1: no more than 5 advantages, no more than 5 disadvantages.
Condition 2: No markdown, no HTML, no special characters.
Only use the provided resources.
"""

GENERATE_DECISION = """
Make a buying decision from the provided original amazon rating, filted reviews data.
Condition 1: The decision should be a boolean (true means should buy, false means should not buy).
Condition 2: The decision should be supported by a reason.
Condition 3: No markdown, no HTML, no special characters.
Only use the provided resources.
"""


def update_key(Firebase):
    key_used_time = Firebase.Get_Gemini_Used_Time()
    if key_used_time == None:
        key_used_time = 0
        Firebase.Update_Gemini_Used_Time(key_used_time)
    else:
        key_used_time = key_used_time + 1
        Firebase.Update_Gemini_Used_Time(key_used_time)
    return key_used_time


def init_gemini(used_time):
    import google.generativeai as genai

    # read gemini "key" from gemini.json in cred
    with open("cred/gemini_keys.json", "r") as file:
        gemini_keys = json.load(file)["keys"]

    # randon key from list of key
    key = gemini_keys[used_time % len(gemini_keys)]

    # print(f"Using key {key}")

    # Set up the API key
    genai.configure(api_key=key)

    # Set up the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest", generation_config=generation_config)

    return model


def gemini_summary(data, amazon_original_rating, Firebase):

    key_used_time = update_key(Firebase)

    model = init_gemini(key_used_time)

    convo = model.start_chat(history=[])
    convo.send_message(
        f"{GENERATE_SUMMARY}\n{JSON_MODEL_SUMMARY}\nAmazon Original Rating: {amazon_original_rating}\nDATA: {data}")
    # print(convo.last.text)
    return convo.last.text


def gemini_reddit_summary(data, product_name, amazon_original_rating, Firebase):

    key_used_time = update_key(Firebase)

    model = init_gemini(key_used_time)

    convo = model.start_chat(history=[])
    convo.send_message(
        f"{GENERATE_REDDIT_SUMMARY}\nProduct Name: {product_name}\n{JSON_MODEL_SUMMARY}\nAmazon Original Rating: {amazon_original_rating}\nDATA: {data}")
    # print(convo.last.text)
    return convo.last.text


def gemini_a_d(data, Firebase):

    key_used_time = update_key(Firebase)

    model = init_gemini(key_used_time)

    convo = model.start_chat(history=[])
    convo.send_message(f"{GENERATE_A_D}\n{JSON_MODEL_A_D}\nDATA: {data}")
    # print(convo.last.text)
    return convo.last.text


def gemini_decision(data, amazon_original_rating, Firebase):

    key_used_time = update_key(Firebase)

    model = init_gemini(key_used_time)

    convo = model.start_chat(history=[])
    convo.send_message(
        f"{GENERATE_DECISION}\n{JSON_MODEL_DECISION}\nAmazon Original Rating: {amazon_original_rating}\nDATA: {data}")
    # print(convo.last.text)
    return convo.last.text


def gemini_extract_json(text_response):
    # This pattern matches a string that starts with '{' and ends with '}'
    pattern = r'\{[^{}]*\}'
    matches = re.finditer(pattern, text_response)
    json_objects = []
    for match in matches:
        json_str = match.group(0)
        try:
            # Validate if the extracted string is valid JSON
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # Extend the search for nested structures
            extended_json_str = gemini_extend_search(
                text_response, match.span())
            try:
                json_obj = json.loads(extended_json_str)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                # Handle cases where the extraction is not valid JSON
                continue
    if json_objects:
        return json_objects
    else:
        return None  # Or handle this case as you prefer


def gemini_extend_search(text, span):
    # Extend the search to try to capture nested structures
    start, end = span
    nest_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            nest_count += 1
        elif text[i] == '}':
            nest_count -= 1
            if nest_count == 0:
                return text[start:i+1]
    return text[start:end]
