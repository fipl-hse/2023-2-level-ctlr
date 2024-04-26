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
    """
    The seed-url is not appropriate.
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Total number of articles is out of range from 1 to 150.
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Total number of articles to parse is not integer.
    """


class IncorrectHeadersError(Exception):
    """
    Headers are not in a form of dictionary.
    """


class IncorrectEncodingError(Exception):
    """
    Encoding must be specified as a string.
    """


class IncorrectTimeoutError(Exception):
    """
    Timeout value must be a positive integer less than 60.
    """


class IncorrectVerifyError(Exception):
    """
    Verify certificate value must either be True or False.
    """


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
        self.conf_dto = self._extract_config_content()
        self._validate_config_content()
        self._seed_urls = self.conf_dto.seed_urls
        self._num_articles = self.conf_dto.total_articles
        self._headers = self.conf_dto.headers
        self._encoding = self.conf_dto.encoding
        self._timeout = self.conf_dto.timeout
        self._should_verify_certificate = self.conf_dto.should_verify_certificate
        self._headless_mode = self.conf_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, "r", encoding="utf-8") as file:
            conf = json.load(file)
        return ConfigDTO(**conf)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """

        if not isinstance(self.conf_dto.seed_urls, list) or not all(
                re.match(r"https?://(www.)?ti71\.ru/news+", seed_url) for seed_url in self.conf_dto.seed_urls):
            raise IncorrectSeedURLError

        if not isinstance(self.conf_dto.total_articles, int) or self.conf_dto.total_articles <= 0:
            raise IncorrectNumberOfArticlesError

        if self.conf_dto.total_articles < 1 or self.conf_dto.total_articles > 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(self.conf_dto.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(self.conf_dto.encoding, str):
            raise IncorrectEncodingError

        if not isinstance(self.conf_dto.timeout, int) or not 0 < self.conf_dto.timeout < 60:
            raise IncorrectTimeoutError

        if not isinstance(self.conf_dto.should_verify_certificate, bool) \
                or not isinstance(self.conf_dto.headless_mode, bool):
            raise IncorrectVerifyError

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
    period = random.randrange(1, 5)
    sleep(period)
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
        self.url_pattern = "https://ti71.ru"

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        for a in article_bs.find_all('a', class_="title-card-news__name"):
            url = self.url_pattern + a.get('href')
            if url not in self.urls:
                break
        else:
            url = ''
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        urls = []
        while len(self.urls) < self.config.get_num_articles():
            for seed_url in self.get_search_urls():
                response = make_request(seed_url, self.config)
                if response.status_code == 200:
                    found = BeautifulSoup(response.text, 'lxml')
                    extr = self._extract_url(found)
                    while extr:
                        self.urls.append(extr)
                        extr = self._extract_url(found)
                    break
        self.urls.extend(urls)


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
        self.article = Article(self.full_url, self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        article_text = [div.text.strip() for div in article_soup.find_all('div', class_='news-detail__detail-text')]
        self.article.text = '\n'.join(article_text)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        title = article_soup.find('h1', class_='news-detail__title')
        self.article.title = title.text
        date = article_soup.find('p', class_='news-detail__date date')
        self.article.date = self.unify_date_format(date.text)
        topics = article_soup.find('p', class_='news-detail__rubric tag tag--large')
        self.article.topics = [topic.text for topic in topics]
        self.article.author = ['NOT FOUND']

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        date_res = ''
        ruen_months = {
            "января": "Jan",
            "февраля": "Feb",
            "марта": "Mar",
            "апреля": "Apr",
            "мая": "May",
            "июня": "Jun",
            "июля": "Jul",
            "августа": "Aug",
            "сентября": "Sep",
            "октября": "Oct",
            "ноября": "Nov",
            "декабря": "Dec"
        }
        for rus, eng in ruen_months.items():
            if rus in date_str:
                date_res = date_str.replace(rus, eng)
        return datetime.datetime.strptime(date_res, '%H:%M, %d %b %Y')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self.config)
        if response.ok:
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
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    conf = Config(CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(conf)
    crawler.find_articles()

    for i, url in enumerate(crawler.urls, 1):
        parser = HTMLParser(url, i, conf)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)


if __name__ == "__main__":
    main()
