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
import time
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
        self.configdto = self._extract_config_content()
        self._validate_config_content()

        self._seed_urls = self.configdto.seed_urls
        self._headers = self.configdto.headers
        self._num_articles = self.configdto.total_articles
        self._encoding = self.configdto.encoding
        self._timeout = self.configdto.timeout
        self._should_verify_certificate = self.configdto.should_verify_certificate
        self._headless_mode = self.configdto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, encoding='utf-8') as file:
            config = json.load(file)
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not isinstance(self.configdto.seed_urls, list):
            raise IncorrectSeedURLError("seed URL should be a list")
        for seed_url in self.configdto.seed_urls:
            if not re.match(r'https?://(www.)?academ\.info/news', seed_url):
                raise IncorrectSeedURLError("seed URL does not match \
                standard pattern 'https?://(www.)?'")

        if not isinstance(self.configdto.total_articles, int) or \
                self.configdto.total_articles <= 0:
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if not 0 < self.configdto.total_articles <= 150:
            raise NumberOfArticlesOutOfRangeError('total number of articles is out of range')

        if not isinstance(self.configdto.headers, dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')

        if not isinstance(self.configdto.encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if not isinstance(self.configdto.timeout, int) or not 0 < self.configdto.timeout < 60:
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')

        if not isinstance(self.configdto.should_verify_certificate, bool) or not \
                isinstance(self.configdto.headless_mode, bool):
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
    time.sleep(random.randrange(1, 4))
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
        self.url_pattern = 'https://academ.info'
        self.urls = []

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        a_tag = article_bs['href']
        return self.url_pattern + a_tag

    def find_articles(self) -> None:
        """
        Find articles.
        """
        for url in self.get_search_urls():
            response = make_request(url, self.config)
            if not response.ok:
                continue
            article_bs = BeautifulSoup(response.text, 'lxml')
            for a in article_bs.find_all('a', class_='dark_link color-theme-target'):
                if len(self.urls) == self.config.get_num_articles():
                    break
                if self._extract_url(a) not in self.urls:
                    self.urls.append(self._extract_url(a))

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
        full_text_from_div = []
        intro = article_soup.find('div', class_='introtext')
        div_blocks = article_soup.find('div', class_='content')
        full_text_from_div.append(intro.text.strip())
        for div_tag in div_blocks:
            full_text_from_div.append(div_tag.text.strip())
        self.article.text = ''.join(full_text_from_div)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        topics = article_soup.find_all('a', class_='breadcrumbs__link')
        for t in topics:
            if t:
                self.article.topics.append(t.text)
        self.article.title = article_soup.title.text
        date = article_soup.find('div', attrs={'class': ['sb-item__date', 'sb-item__time']})
        if date:
            self.article.date = self.unify_date_format(date.text)
        self.article.author = ['NOT FOUND']

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        months = {"января": "Jan", "февраля": "Feb", "марта": "Mar",
                  "апреля": "Apr", "мая": "May", "июня": "Jun", "июля": "Jul",
                  "августа": "Aug", "сентября": "Sep", "октября": "Oct", "ноября": "Nov",
                  "декабря": "Dec"}
        if ":" in date_str:
            today = datetime.date.today()
            hour, minute = map(int, date_str.split(":"))
            d = datetime.datetime(year=today.year, month=today.month,
                                  day=today.day, hour=hour,
                                  minute=minute)
        else:
            day, mon, year = date_str.replace(',', '').split(' ')
            d_str = f'{day} {months[mon]} {year}'
            d = datetime.datetime.strptime(d_str, "%d %b %Y")
        return d

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
        base_path.parent.mkdir()
        base_path.mkdir()
    else:
        base_path.parent.mkdir()
        base_path.mkdir()


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
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


if __name__ == "__main__":
    main()
