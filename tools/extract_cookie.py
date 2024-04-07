import json

# read input from my_cookies.json
with open('my_cookies.json', 'r') as f:
    cookie_json = f.read()

# Load the JSON string
cookie_data = json.loads(cookie_json)

# Extract cookies and convert to { name: value } JSON format
extracted_cookies = {}
for cookie in cookie_data['cookies']:
    extracted_cookies[cookie['name']] = cookie['value']

# Convert extracted cookies to JSON string
extracted_cookies_json = json.dumps(extracted_cookies, indent=4)

# Print the result
print(extracted_cookies_json)
