import requests
from requests.auth import HTTPBasicAuth

url = "https://snapmaker.zendesk.com/api/v2/ticket_metrics?page=40"
url2= "https://snapmaker.zendesk.com/api/v2/tickets/564248.json"
headers = {
	"Content-Type": "application/json",
}
email_address = 'jasmine.xie@snapmaker.com'
api_token = '1vQwYoPB0GhURF2o49wl4xB4KP3LMs8QEoOISkyM'
auth = HTTPBasicAuth(f'{email_address}/token', api_token)

response = requests.request(
	"GET",
	url2,
	auth=auth,
	headers=headers
)

print(response.text)

