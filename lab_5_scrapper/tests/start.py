import requests

headers = {
    'cookie': 'stg_traffic_source_priority=4; stg_externalReferrer=https://www.google.com/; stg_last_interaction=Mon%2C%2008%20Apr%202024%2009:22:24%20GMT; stg_returning_visitor=Mon%2C%2008%20Apr%202024%2009:22:24%20GMT',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}
response = requests.get(
    url='https://www.mk.ru/news/',
    verify=False,
    headers=headers
)
print(response.status_code)
