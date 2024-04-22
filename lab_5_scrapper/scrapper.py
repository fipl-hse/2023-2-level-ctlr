"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
from typing import Pattern, Union
import requests
import json
import re
from core_utils.config_dto import ConfigDTO
from bs4 import BeautifulSoup


class IncorrectSeedURLError(Exception):
    """
    Raising an error when a seed URL does not match standard pattern https?://(www.)?
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Raising an error when the total number of articles is out of range from 1 to 150;
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Raising an error when the total number of articles to parse is not integer
    """


class IncorrectHeadersError(Exception):
    """
    Raising an error when headers are not in a form of dictionary;
    """


class IncorrectEncodingError(Exception):
    """
    Raising an error when encoding is not a string;
    """


class IncorrectTimeoutError(Exception):
    """
    Raising an error when the timeout value is not a positive integer less than 60;
    """


class IncorrectVerifyError(Exception):
    """
    Raising an error when verify certificate is not boolean
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
        self._path_to_config = path_to_config
        self._validate_config_content()
        self._config = self._extract_config_content()

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        file = json.load(open(self._path_to_config))

        config = ConfigDTO(
            seed_urls=file['seed_urls'],
            headers=file['headers'],
            total_articles_to_find_and_parse=file['total_articles_to_find_and_parse'],
            encoding =file['encoding'],
            timeout=file['timeout'],
            should_verify_certificate=file['should_verify_certificate'],
            headless_mode=file['headless_mode']
        )
        return config


    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = json.load(open(self._path_to_config))
        if not isinstance(config['seed_urls'], list) or \
                not all(re.match("https?://(www.)?", x) for x in config['seed_urls']):
            raise IncorrectSeedURLError

        num = config['total_articles']
        if not (1 <= num <= 150):
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(num, int):
            raise IncorrectNumberOfArticlesError

        if not isinstance(config['headers'], dict):
            raise IncorrectHeadersError

        if not isinstance(config['encoding'], str):
            raise IncorrectEncodingError

        if not isinstance(config['timeout'], int) or not (0 < config['timeout'] < 60):
            raise IncorrectTimeoutError

        if not isinstance(config['should_verify_certificate'], bool):
            raise IncorrectVerifyError

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """
        return self._config.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self._config.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return  self._config.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self._config.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self._config.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self._config.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self._config.headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
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

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """

    def find_articles(self) -> None:
        """
        Find articles.
        """

    def get_search_urls(self) -> list:
        """
        Get seed_urls param.

        Returns:
            list: seed_urls param
        """


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
    assets_path = pathlib.Path(base_path) / 'ASSETS_PATH'
    if not assets_path.exists():
        assets_path.mkdir(parents=True, exist_ok=True)
    else:
        for file in assets_path.iterdir():
            file.unlink()
            file.rmdir()


def main() -> None:
    """
    Entrypoint for scrapper module.
    """


if __name__ == "__main__":
    main()
