"""
Crawler implementation.
"""
import datetime
import json
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH
from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
from bs4 import BeautifulSoup
from random import randrange
import shutil
import time
from typing import Pattern, Union
import requests


class IncorrectSeedURLError(Exception):
    """
    seed URL does not match standard pattern "https?://(www.)?"
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    total number of articles is out of range from 1 to 150
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    total number of articles to parse is not integer
    """


class IncorrectHeadersError(Exception):
    """
    headers are not in a form of dictionary
    """


class IncorrectEncodingError(Exception):
    """
    encoding must be specified as a string
    """


class IncorrectTimeoutError(Exception):
    """
    timeout value must be a positive integer less than 60
    """


class IncorrectVerifyError(Exception):
    """
    verify certificate value must either be True or False
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
        self.config = self._extract_config_content()


    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as file:
            config_dto = json.load(file)
        return ConfigDTO(seed_urls=config_dto["seed_urls"],
            total_articles_to_find_and_parse=config_dto["total_articles_to_find_and_parse"],
            headers=config_dto["headers"], encoding=config_dto["encoding"],
            timeout=config_dto["timeout"],
            should_verify_certificate=config_dto["should_verify_certificate"],
            headless_mode=config_dto["headless_mode"])

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()
        if not all(seed.startswith('https://2051.vision/') for seed in config.seed_urls):
            raise IncorrectSeedURLError
        if config.total_articles < 1 or config.total_articles > 150:
            raise NumberOfArticlesOutOfRangeError
        if not isinstance(config.total_articles, int) or self.config.total_articles <= 0:
            raise IncorrectNumberOfArticlesError
        if not isinstance(config.headers, dict):
            raise IncorrectHeadersError
        if not isinstance(config.encoding, str):
            raise IncorrectEncodingError
        if not isinstance(config.timeout, int) or config.timeout <= 0 or config.timeout >= 60:
            raise IncorrectTimeoutError
        if not isinstance(config.should_verify_certificate, bool):
            raise IncorrectVerifyError
        if not isinstance(config.headless_mode, bool):
            raise IncorrectVerifyError

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self.config.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self.config.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self.config.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self.config.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self.config.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self.config.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self.config.headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
    time.sleep(randrange(3))
    return requests.get(url, headers=config.get_headers(), timeout=config.get_timeout())


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

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        return article_bs.find('a')['href']

    def find_articles(self) -> None:
        """
        Find articles.
        """

        for url in self.get_search_urls():
            response = make_request(url, self.config)
            bs = BeautifulSoup(response.text, 'lxml')
            for tag in bs.find_all('h3'):
                if self._extract_url(tag) not in self.urls:
                    self.urls.append(self._extract_url(tag))
                if len(self.urls) == (self.config.get_num_articles()):
                    break

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
        tag = article_soup.find('div', {"id": "wtr-content"})
        raw_texts = tag.find_all('p')
        texts = []
        for text in raw_texts:
            texts.append(text.text)
        self.article.text = '\n'.join(texts)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.title = article_soup.find(class_="tdb-title-text").text
        self.article.topics = article_soup.find_all(class_="tdb-entry-crumb")[1].text
        self.article.author = article_soup.find(class_="tdb-author-name").text
        self.article.date = self.unify_date_format(article_soup.find("time").text)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        date_str = date_str[:-4] + date_str[-2:]
        return datetime.datetime.strptime(date_str, "%d.%m.%y")

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
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(config)
    crawler.find_articles()
    for i, url in enumerate(crawler.urls):
        parser = HTMLParser(url, i+1, config)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)


if __name__ == "__main__":
    main()
