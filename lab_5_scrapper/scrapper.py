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

from core_utils import constants
from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO


class IncorrectSeedURLError(Exception):
    """
    Seed URL does not match standard pattern
    """
class NumberOfArticlesOutOfRangeError(Exception):
    """
    Total number of articles is out of range from 1 to 150
    """
class IncorrectNumberOfArticlesError(Exception):
    """
    Total number of articles to parse is not integer
    """
class IncorrectHeadersError(Exception):
    """
    Headers are not in a form of dictionary
    """
class IncorrectEncodingError(Exception):
    """
    Encoding is not specified as a string
    """
class IncorrectTimeoutError(Exception):
    """
    Timeout value is not a positive integer less than 60
    """
class IncorrectVerifyError(Exception):
    """
    Verify certificate value is not True or False
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
        self._validate_config_content()
        self.config_dto = self._extract_config_content()

        self._seed_urls = self.config_dto.seed_urls
        self._num_articles = self.config_dto.total_articles
        self._headers = self.config_dto.headers
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
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if not isinstance(config['seed_urls'], list):
            raise IncorrectSeedURLError

        if not (isinstance(config['seed_urls'], list)
                and all(re.match(r'https?://(www.)?', seed_url) for seed_url in config['seed_urls'])):
            raise IncorrectSeedURLError

        if (not isinstance(config['total_articles_to_find_and_parse'], int) or
                config['total_articles_to_find_and_parse'] <= 0):
            raise IncorrectNumberOfArticlesError

        if not 0 < config['total_articles_to_find_and_parse'] <= 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config['headers'], dict):
            raise IncorrectHeadersError

        if not isinstance(config['encoding'], str):
            raise IncorrectEncodingError

        if not isinstance(config['timeout'], int) or not 0 < config['timeout'] < 60:
            raise IncorrectTimeoutError

        if (not isinstance(config['should_verify_certificate'], bool) or
                not isinstance(config['headless_mode'], bool)):
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
    period = random.randrange(5)
    time.sleep(period)

    response = requests.get(url=url, timeout=config.get_timeout(),
                            headers=config.get_headers(),
                            verify=config.get_verify_certificate())
    return response


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
        self.urls = []
        self.config = config
        self.url_pattern = 'https://elementy.ru/novosti_nauki'
        #self.url_pattern = 'https://vse42.ru/articles'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """

        #link = article_bs.find('a').get('href')
        #url = self.url_pattern + link[len('/articles')::]
        #print(url)

        link = article_bs.find('a', class_='nohover').get('href')
        url = self.url_pattern + link[len('/novosti_nauki')::]
        print(url)

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()
        for seed_url in seed_urls:
            response = make_request(seed_url, self.config)

            if not response.ok:
                continue

            article_bs = BeautifulSoup(response.text, 'html.parser')
            for link in article_bs.find(class_='clblock newslist').find_all(class_='img_block32'):
                if len(self.urls) == self.config.get_num_articles():
                    break
                if self._extract_url(link) and self._extract_url(link) not in self.urls:
                    self.urls.append(self._extract_url(link))

            #for link in article_bs.find(class_='').find_all(class_='list-item'):
            #    if len(self.urls) == self.config.get_num_articles():
            #        break
            #    if self._extract_url(link) and self._extract_url(link) not in self.urls:
            #        self.urls.append(self._extract_url(link))
#
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
        paragraphs = article_soup.find_all('p')
        self.article_text = "\n".join([p.get_text() for p in paragraphs])

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self.config)
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            self._fill_article_with_text(soup)
            self._fill_article_with_meta_information(soup)

        return self.article


def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    base_path = pathlib.Path(base_path)
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    configuration = Config(path_to_config=constants.CRAWLER_CONFIG_PATH)
    crawler = Crawler(configuration)
    base_path = constants.ASSETS_PATH
    prepare_environment(base_path)
    crawler.find_articles()


if __name__ == "__main__":
    main()
