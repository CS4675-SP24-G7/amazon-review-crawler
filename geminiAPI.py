import os
import google.generativeai as genai
import requests
from dotenv import load_dotenv, dotenv_values, find_dotenv


genai.configure(api_key=os.getenv("APIKEY"))

# Set up the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config)




model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config)





def geminiApiCall(data):

    convo = model.start_chat(history=[])
    convo.send_message("Make me a JSON data with the key Summary, Advantage, and Disadvantage. Give me a summary of less than 5 sentences, less than 5 advantages, less than 5 disadvantages. Put advantage and disadvantages in an array. Only use the provided resources. Do not Make it MarkDown! \n" + data)
    # convo.send_message("Using the following data, give me 3 sentence summary and give me 2 advantage and two disadvantage of the product. Do not use any other outside resource. Use only the data. \n" + data)
    print(convo.last.text)
    return convo.last.text