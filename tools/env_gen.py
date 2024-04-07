import base64
import json
from dotenv import load_dotenv, find_dotenv
import os

# firebase_key = {}

# service_key = json.dumps(firebase_key)

# # # encode service key
# encoded_service_key = base64.b64encode(service_key.encode('utf-8'))

# print(encoded_service_key)

# load_dotenv(find_dotenv())

# encoded_key = os.getenv("SERVICE_ACCOUNT_KEY")

# # remove the first two chars and the last char in the key
# encoded_key = str(encoded_key)[2:-1]

# # decode
# original_service_key = json.loads(
#     base64.b64decode(encoded_key).decode('utf-8'))

# print(original_service_key['private_key_id'])
