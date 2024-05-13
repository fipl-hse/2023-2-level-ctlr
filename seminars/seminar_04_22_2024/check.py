import requests
from bs4 import BeautifulSoup
import datetime

correct_url = 'https://www.vokrugsveta.ru/articles/skolko-nuzhno-chasov-sna-chtoby-snizit-risk-diabeta-raschety-i-vyvody-uchenykh-id5632353/'
response = requests.get(correct_url)

article_soup = BeautifulSoup(response.text, 'lxml')

author = article_soup.find('span', class_="ds-article-footer-authors__author")
if author:
    print(author.text)
else:
    print("None")

title = article_soup.find(itemprop="headline").text.strip()
print(title)

date = article_soup.find(class_='ds-article-header-date-and-stats__date').text.strip()
parts = date.split()
month = parts[1].capitalize()
formatted_date = f"{parts[0]} {month} {parts[2]}"

months_dict = {
            'Января': 'January',
            'Февраля': 'February',
            'Марта': 'March',
            'Апреля': 'April',
            'Мая': 'May',
            'Июня': 'June',
            'Июля': 'July',
            'Августа': 'August',
            'Сентября': 'September',
            'Октября': 'October',
            'Ноября': 'November',
            'Декабря': 'December'
        }

for month_ru, month_en in months_dict.items():
    formatted_date = formatted_date.replace(month_ru, month_en)

print(datetime.datetime.strptime(formatted_date, '%d %B %Y'))

list_of_keywords = []
keywords = article_soup.find_all(itemprop="articleSection")

for i in keywords:
    list_of_keywords.append(i.text)

print(list_of_keywords)


