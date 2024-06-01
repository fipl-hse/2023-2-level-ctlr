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

from core_utils import constants
from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO


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
        self._validate_config_content()
        self.config = self._extract_config_content()
        self._seed_urls = self.config.seed_urls
        self._num_articles = self.config.total_articles
        self._headers = self.config.headers
        self._encoding = self.config.encoding
        self._timeout = self.config.timeout
        self._should_verify_certificate = self.config.should_verify_certificate
        self._headless_mode = self.config.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        config = json.load(self.path_to_config.open())
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()
        if not (isinstance(config.seed_urls, list)
                and all(re.match(r'https://antropogenez.ru/news/', seed_url)
                        for seed_url in config.seed_urls
                        )
                ):
            raise IncorrectSeedURLError
        if not isinstance(config.total_articles, int) or config.total_articles <= 0:
            raise IncorrectNumberOfArticlesError
        if not 0 < config.total_articles <= constants.NUM_ARTICLES_UPPER_LIMIT:
            raise NumberOfArticlesOutOfRangeError
        if not isinstance(config.headers, dict):
            raise IncorrectHeadersError
        if not isinstance(config.encoding, str):
            raise IncorrectEncodingError
        if not isinstance(config.timeout, int):
            raise IncorrectTimeoutError
        if (config.timeout <= constants.TIMEOUT_LOWER_LIMIT
                or config.timeout > constants.TIMEOUT_UPPER_LIMIT):
            raise IncorrectTimeoutError
        if not isinstance(config.headless_mode, bool):
            raise IncorrectVerifyError
        if not isinstance(config.should_verify_certificate, bool):
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
    sleep(random.randrange(3))

    return requests.get(
        url=url,
        timeout=config.get_timeout(),
        headers=config.get_headers(),
        verify=config.get_verify_certificate(),
        encoding=config.get_encoding()
    )


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
        self.url_pattern = 'https://antropogenez.ru/news/'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        url = ''
        list_of_links = article_bs.find_all('h2')
        for link in list_of_links:
            url = link.find('a')['href']
            if url not in self.urls:
                break
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()

        while len(self.urls) < self.config.get_num_articles():
            for seed_url in seed_urls:
                response = make_request(seed_url, self.config)
                if not response.ok:
                    continue
                self.urls.append(self._extract_url(BeautifulSoup(response.text, "lxml")))

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
        raw_text = ''
        text_blocks = article_soup.find_all('p')
        for text_block in text_blocks:
            if text_block.string:
                raw_text += text_block.string

        self.article.text = raw_text

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        headline = article_soup.find("h1")
        if not headline:
            self.article.title = "NOT FOUND"
        else:
            self.article.title = headline.text

        author = article_soup.find("a", href='/redactor/')
        if not author:
            self.article.author = ["NOT FOUND"]
        else:
            self.article.author = [author.text]

        found_date = article_soup.find('meta', {'name': "date"})
        date = found_date['content']
        if date:
            self.article.date = self.unify_date_format(date)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

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
    configuration = Config(constants.CRAWLER_CONFIG_PATH)

    prepare_environment(constants.ASSETS_PATH)

    crawler = Crawler(config=configuration)
    crawler.find_articles()
    urls = crawler.urls

    for index, url in enumerate(urls):
        parser = HTMLParser(full_url=url, article_id=index + 1, config=configuration)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)
    print("Done")


if __name__ == "__main__":
    main()
