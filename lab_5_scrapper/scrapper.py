"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import json
import pathlib
import re
import shutil
from datetime import datetime
from random import randrange
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
    The seed url is not alike the pattern.
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    The number of articles is not in range of 1 to 150.
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    The article number is not integer.
    """


class IncorrectHeadersError(Exception):
    """
    The headers are not stored in a dictionary.
    """


class IncorrectEncodingError(Exception):
    """
    The encoding is not a string.
    """


class IncorrectTimeoutError(Exception):
    """
    The timeout is not an integer or is not in the range.
    """


class IncorrectVerifyError(Exception):
    """
    Verification check or Headless mode are not boolean.
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
        self.config = self._extract_config_content()
        self._validate_config_content()

        self._encoding = self.config.encoding
        self._headers = self.config.headers
        self._headless_mode = self.config.headless_mode
        self._num_articles = self.config.total_articles
        self._seed_urls = self.config.seed_urls
        self._should_verify_certificate = self.config.should_verify_certificate
        self._timeout = self.config.timeout

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            confi = json.load(f)

        return ConfigDTO(**confi)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()

        if not isinstance(config.seed_urls, list):
            raise IncorrectSeedURLError

        for seed_url in config.seed_urls:
            if not re.match(r"https?://(www.)?vtomske\.ru", seed_url):
                raise IncorrectSeedURLError

        if not isinstance(config.total_articles, int) or config.total_articles <= 0:
            raise IncorrectNumberOfArticlesError

        if config.total_articles > 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(config.encoding, str):
            raise IncorrectEncodingError

        if not isinstance(config.timeout, int) or not 0 <= config.timeout < 60:
            raise IncorrectTimeoutError

        if (not isinstance(config.should_verify_certificate, bool)
                or not isinstance(config.headless_mode, bool)):
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
    sleep(randrange(3))

    return requests.get(
        url=url,
        timeout=config.get_timeout(),
        headers=config.get_headers(),
        verify=config.get_verify_certificate()
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
        self.base_url = "https://vtomske.ru"

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """

        link = article_bs.find(class_='mainbar')
        if link:
            links = link.find_all('a')
            for link in links:
                href = link.get('href')
                if href:
                    url = self.base_url + href
                    if url not in self.get_search_urls() and url not in self.urls:
                        return url
        return ''

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()

        for seed_url in seed_urls:
            response = make_request(seed_url, self.config)
            if not response.ok:
                continue

            article_soup = BeautifulSoup(response.text, features='lxml')
            new_url = self._extract_url(article_soup)
            while new_url:
                if len(self.urls) == self.config.get_num_articles():
                    break
                self.urls.append(new_url)
                new_url = self._extract_url(article_soup)

            if len(self.urls) == self.config.get_num_articles():
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
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        body = article_soup.find('div', class_='material-content')
        if body:
            content = body.find_all('p')
            self.article.text = '\n'.join([p_tag.text for p_tag in content])

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        cont = article_soup.find('div', class_='material-content')
        if cont:
            title = cont.find('h1')
            if title:
                self.article.title = title.text

        author = article_soup.find('a', class_='material-author')
        if not author:
            self.article.author.append('NOT FOUND')
        else:
            self.article.author.append(author.text.strip())

        date = article_soup.find('time', class_='material-date')
        if date:
            date_str = date.attrs.get('datetime')
            if isinstance(date_str, str):
                self.article.date = self.unify_date_format(date_str)

        tags = article_soup.find_all(class_='material-tags')
        for tag in tags:
            self.article.topics.append(tag.text)

    def unify_date_format(self, date_str: str) -> datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self.config)
        if response.ok:
            article_bs = BeautifulSoup(response.text, features='html.parser')
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
    crawler = Crawler(configuration)
    prepare_environment(constants.ASSETS_PATH)

    crawler.find_articles()
    i = 1
    for url in crawler.urls:
        parser = HTMLParser(full_url=url, article_id=i, config=configuration)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)
            i += 1


if __name__ == "__main__":
    main()
