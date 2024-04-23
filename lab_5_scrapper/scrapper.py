"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import re
import shutil
from pathlib import Path
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import (ASSETS_PATH, CRAWLER_CONFIG_PATH,
                                  NUM_ARTICLES_UPPER_LIMIT,
                                  TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT)

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
        self._validate_config_content()
        self._config_dto = self._extract_config_content()
        self._seed_urls = self._config_dto.seed_urls
        self._num_articles = self._config_dto.total_articles
        self._headers = self._config_dto.headers
        self._encoding = self._config_dto.encoding
        self._timeout = self._config_dto.timeout
        self._should_verify_certificate = self._config_dto.should_verify_certificate
        self._headless_mode = self._config_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """

        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return ConfigDTO(
            config["seed_urls"],
            config["total_articles_to_find_and_parse"],
            config["headers"],
            config["encoding"],
            config["timeout"],
            config["should_verify_certificate"],
            config["headless_mode"],
        )

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config_dto = self._extract_config_content()
        if not isinstance(config_dto.seed_urls, list):
            raise IncorrectSeedURLError

        for url in config_dto.seed_urls:
            if not re.match(r"https?://(www.)?", url) or not isinstance(url, str):
                raise IncorrectSeedURLError

        total_articles = config_dto.total_articles
        if not isinstance(total_articles, int) \
                or total_articles < 1:
            raise IncorrectNumberOfArticlesError

        if total_articles > NUM_ARTICLES_UPPER_LIMIT:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config_dto.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(config_dto.encoding, str):
            raise IncorrectEncodingError

        timeout = config_dto.timeout
        if not isinstance(timeout, int) or timeout <= TIMEOUT_LOWER_LIMIT or timeout >= TIMEOUT_UPPER_LIMIT:
            raise IncorrectTimeoutError

        should_verify = config_dto.should_verify_certificate
        if not isinstance(should_verify, bool) or not isinstance(config_dto.headless_mode, bool):
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
        return self._config_dto.headers

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
    response = requests.get(url, headers=config.get_headers(), timeout=config.get_timeout(),
                            verify=config.get_verify_certificate())
    response.encoding = config.get_encoding()
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
        self._config = config
        self._seed_urls = config.get_seed_urls()
        self.urls = []

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        href = article_bs.get("href")

        if href and href.startswith("https://www.comnews.ru/") and 'longreads' not in href \
                and '__site/about/' not in href:
            return str(href)
        return ""

    def find_articles(self) -> None:
        """
        Find articles.
        """
        for seed_url in self._seed_urls:
            response = make_request(seed_url, self._config)
            soup = BeautifulSoup(response.text, "lxml")
            for paragraph in soup.find_all('a'):
                if len(self.urls) >= self._config.get_num_articles():
                    return
                url = self._extract_url(paragraph)
                if not url or url in self.urls:
                    continue

                self.urls.append(url)

    def get_search_urls(self) -> list:
        """
        Get seed_urls param.

        Returns:
            list: seed_urls param
        """
        return self._seed_urls


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
        self._config = config
        self.article = Article(self.full_url, self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """


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

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """


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


if __name__ == "__main__":
    main()
