import os
import google.generativeai as genai
import re
import json

genai.configure(api_key=os.getenv("APIKEY"))

# Set up the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest", generation_config=generation_config)

JSON_MODEL_A_D = """
Provide a response in a structured JSON format that matches the following model:
{"advantages": ["advantage 1", "advantage 2", "advantage 2", ...],
"disadvantages": ["disadvantage 1", "disadvantage 2", "disadvantage 3", ...]}
"""

JSON_MODEL_SUMMARY = """
Provide a response in a structured JSON format that matches the following model:
{"summary": ""}
"""

GENERATE_SUMMARY = """
Make a summary from the provided reviews data. 
Condition 1: Give me a summary of no more than 10 sentences.
Only use the provided resources.
"""

GENERATE_A_D = """
Make me Advantage, and Disadvantage from the provided reviews data. 
Condition 1: no more than 5 advantages, no more than 5 disadvantages.
Only use the provided resources.
"""

# ORIGINAL = """
# Make me a JSON data with the key Summary, Advantage, and Disadvantage.
# Give me a summary of less than 5 sentences, less than 5 advantages, less than 5 disadvantages.
# Put advantage and disadvantages in an array.
# Only use the provided resources.
# """


def gemini_summary(data):
    convo = model.start_chat(history=[])
    convo.send_message(
        f"{GENERATE_SUMMARY}\n{JSON_MODEL_SUMMARY}\nDATA: {data}")
    print(convo.last.text)
    return convo.last.text


def gemini_a_d(data):
    convo = model.start_chat(history=[])
    convo.send_message(f"{GENERATE_A_D}\n{JSON_MODEL_A_D}\nDATA: {data}")
    print(convo.last.text)
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
            extended_json_str = extend_search(text_response, match.span())
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


def extend_search(text, span):
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
