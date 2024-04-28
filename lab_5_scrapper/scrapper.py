"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import random
import re
import shutil
from time import sleep
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH


class IncorrectSeedURLError(Exception):
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    pass


class IncorrectNumberOfArticlesError(Exception):
    pass


class IncorrectHeadersError(Exception):
    pass


class IncorrectEncodingError(Exception):
    pass


class IncorrectTimeoutError(Exception):
    pass


class IncorrectVerifyError(Exception):
    pass


class Config:
    """
    Class for unpacking and validating configurations.
    """

    def __init__(self, path_to_config: pathlib.Path) -> None:
        """
        Initialize an instance of the Config class.

        Args:
            path_to_config (pathlib.Path): Path to configuration.
        """
        self.path_to_config = path_to_config
        self.config_dto = self._extract_config_content()
        self._validate_config_content()

        self._seed_urls = self.config_dto.seed_urls
        self._headers = self.config_dto.headers
        self._num_articles = self.config_dto.total_articles
        self._encoding = self.config_dto.encoding
        self._timeout = self.config_dto.timeout
        self._should_verify_certificate = self.config_dto.should_verify_certificate
        self._headless_mode = self.config_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config) as file:
            config_dto = json.load(file)
        return ConfigDTO(**config_dto)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not isinstance(self.config_dto.seed_urls, list):
            raise IncorrectSeedURLError('"seed_urls" is not a list')

        for url in self.config_dto.seed_urls:
            if not re.match(r"https?://(www.)?vremyan\.ru/analitycs", url):
                raise IncorrectSeedURLError('seed URL does not match standard pattern')

        if not isinstance(self.config_dto.total_articles, int) or self.config_dto.total_articles <= 0:
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if not 1 <= self.config_dto.total_articles <= 150:
            raise NumberOfArticlesOutOfRangeError('total number of articles is out of range')

        if not isinstance(self.config_dto.headers, dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')

        if not isinstance(self.config_dto.encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if not isinstance(self.config_dto.timeout, int) or not 1 <= self.config_dto.timeout < 60:
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')

        if (not isinstance(self.config_dto.should_verify_certificate, bool) or not
                isinstance(self.config_dto.headless_mode, bool)):
            raise IncorrectVerifyError('verify certificate value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self._seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self._num_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self._headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self._encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self._timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self._should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self._headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
    sleep(random.randrange(1, 2))
    return requests.get(url=url,
                        headers=config.get_headers(),
                        timeout=config.get_timeout(),
                        verify=config.get_verify_certificate())


class Crawler:
    """
    Crawler implementation.
    """

    url_pattern: Union[Pattern, str]

    def __init__(self, config: Config) -> None:
        """
        Initialize an instance of the Crawler class.

        Args:
            config (Config): Configuration
        """
        self.config = config
        self.urls = []
        self.url_pattern = 'https://www.vremyan.ru'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        return f'{self.url_pattern}{article_bs.get("href")}'

    def find_articles(self) -> None:
        """
        Find articles.
        """
        for i in self.get_search_urls():
            response = make_request(i, self.config)
            if not response.ok:
                continue
            obj = BeautifulSoup(response.text, 'lxml')
            for div in obj.find_all('div', class_="news-list moreLoadedCell"):
                for a in div.find_all('a'):
                    if len(self.urls) == self.config.get_num_articles():
                        break
                    url = self._extract_url(a)
                    if url not in self.urls:
                        self.urls.append(url)

    def get_search_urls(self) -> list:
        """
        Get seed_urls param.

        Returns:
            list: seed_urls param
        """
        return self.config.get_seed_urls()


# 10
# 4, 6, 8, 10


class HTMLParser:
    """
    HTMLParser implementation.
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initialize an instance of the HTMLParser class.

        Args:
            full_url (str): Site url
            article_id (int): Article id
            config (Config): Configuration
        """
        self.full_url = full_url
        self.article_id = article_id
        self.config = config
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        article_soup_list = article_soup.find('article').find_all(['p', 'h4'],
                                                             style=["text-align:justify",
                                                                    "text-align:center"])
        text_list = []
        for el in article_soup_list:
            text_list.append(el.text)
        self.article.text = ''.join(text_list)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """

        self.article.title = article_soup.find('h1', class_=['ro-1', 'short-header']).text
        self.article.article_id = self.article_id
        self.article.author = ['NOT FOUND']
        self.article.date = self.unify_date_format(article_soup.find('p', class_='desc').text)
        topics = article_soup.find('a', class_='label')
        if topics:
            self.article.topics = [article_soup.find('a', class_='label').text]

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """

        months_dict = {
            "января": "January",
            "февраля": "February",
            "марта": "March",
            "апреля": "April",
            "мая": "May",
            "июня": "June",
            "июля": "July",
            "августа": "August",
            "сентября": "September",
            "октября": "October",
            "ноября": "November",
            "декабря": "December"
        }

        MY_DATE_FORMAT = "%d %B %Y года, %H:%M"

        for rus_month, eng_month in months_dict.items():
            date_str = date_str.replace(rus_month, eng_month)

        count = 0
        for el in reversed(date_str):
            if not el.isdigit():
                count += 1
            else:
                break

        date_str = date_str[:-count]

        if date_str:
            date = datetime.datetime.strptime(date_str, MY_DATE_FORMAT)
            return date

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self.config)
        article_bs = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)

        return self.article


def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    if base_path.exists():
        shutil.rmtree(base_path.parent)
    base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """


if __name__ == "__main__":
    main()

configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
prepare_environment(ASSETS_PATH)
crawler = Crawler(config=configuration)
crawler.find_articles()

for i, full_url in enumerate(crawler.urls, 1):
    parser = HTMLParser(full_url=full_url, article_id=i, config=configuration)
    article = parser.parse()
    if isinstance(article, Article):
        to_raw(article)
        to_meta(article)