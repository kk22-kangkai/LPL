import requests

url = "https://api.snapmaker.cn/api/oauth2/token?grant_type=snapmaker_device&productCode=LAVATEST123&sn=0&sign=5md2o%2FQAWDoP1MIN2RSrl%2BXbtV4UaMJJg3qmJrY4qJFwcAqvbUwXjBr0zCg2dFPO&nonce=428170&refresh=true"

payload = {}
headers = {
  'Authorization': 'Basic bWFsbC1hcHA6MTIzNDU2'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
