"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
import json
import shutil
import datetime
import re
from typing import Pattern, Union
import requests
from bs4 import BeautifulSoup
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH

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

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding = 'utf-8') as f:
            config = json.load(f)
        return ConfigDTO

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        valid_url = self.config_dto.seed_urls
        if not valid_url.startswith("https?://(www.)?") and not isinstance(valid_url, str):
            raise IncorrectSeedURLError

        number_articles = self.config_dto.total_articles
        if number_articles > 150 or number_articles < 1:
            raise NumberOfArticlesOutOfRangeError
        if number_articles <= 0 or not isinstance(number_articles, int):
            raise IncorrectNumberOfArticlesError

        headers_articles = self.config_dto.headers
        if not isinstance(headers_articles, dict):
            raise IncorrectHeadersError
        encode_articles = self.config_dto.encoding
        if not isinstance(encode_articles, str):
            raise IncorrectEncodingError

        timeout_articles = self.config_dto.timeout
        if timeout_articles > 60 or timeout_articles < 0:
            raise IncorrectTimeoutError

        certificate_articles = self.config_dto.should_verify_certificate
        headless_articles = self.config_dto.headless_mode
        if not isinstance(certificate_articles, bool) or not isinstance (headless_articles, bool):
            raise IncorrectVerifyError

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self._seed_urls()

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
        return self._verify_certificate

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
    return requests.get(url = url, timeout = config.get_timeout(), headers = config.get_headers(), verify = config.get_verify_certificate())

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
        all_links = article_bs.find_all('a', #???)
        for link in all_links:
            url = link['href']
        ###i dont know what to do here :(

    def find_articles(self) -> None:
        """
        Find articles.
        """

        while len(self_url) < self.config.get_num_articles():
            for seed_url in self.get_search_urls():
                response = make_request(seed_url, self.config)
                if not response.ok:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                extra_urls = self._extract_url(soup)
                self.urls.append(extra_urls)

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
        shutil.rmtree(base_path.parent)
    base_path.mkdir(parents=True)

def main() -> None:
    """
    Entrypoint for scrapper module.
    """


if __name__ == "__main__":
    main()
