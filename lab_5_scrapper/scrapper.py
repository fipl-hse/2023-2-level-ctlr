"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import re
import shutil
from bs4 import BeautifulSoup
import requests
from typing import Pattern, Union
from core_utils import constants
from core_utils.article.io import to_raw
from core_utils.article.article import Article
from core_utils.config_dto import ConfigDTO


class IncorrectSeedURLError(Exception):
    pass


class IncorrectNumberOfArticlesError(Exception):
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    pass


class IncorrectHeadersError(Exception):
    pass


class IncorrectEncodingError(Exception):
    pass


class IncorrectVerifyError(Exception):
    pass


class IncorrectTimeoutError(Exception):
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
        with open(self.path_to_config, "r", encoding="utf-8") as f:
            conf = json.load(f)
        return ConfigDTO(
            seed_urls=conf["seed_urls"],
            total_articles_to_find_and_parse=conf["total_articles_to_find_and_parse"],
            headers=conf["headers"],
            encoding=conf["encoding"],
            timeout=conf["timeout"],
            should_verify_certificate=conf["should_verify_certificate"],
            headless_mode=conf["headless_mode"])

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()

        if not (isinstance(config.seed_urls, list)
                and all(re.match(r"https?://(www.)?", seed_url) for seed_url in config.seed_urls)):
            raise IncorrectSeedURLError

        num = config.total_articles
        if not isinstance(num, int) or num <= 0:
            raise IncorrectNumberOfArticlesError
        if num > 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(config.encoding, str):
            raise IncorrectEncodingError

        if not isinstance(config.should_verify_certificate, bool) \
                or not isinstance(config.headless_mode, bool):
            raise IncorrectVerifyError

        if not isinstance(config.timeout, int) \
                or config.timeout > 60 or config.timeout < 0:
            raise IncorrectTimeoutError

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
    return requests.get(url=url, timeout=config.get_timeout(),
                        headers=config.get_headers(), verify=config.get_verify_certificate())


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
        self.url_pattern = 'https://ug.ru/category/all-news/'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        url = ""
        links = article_bs.find_all('a', class_='category-post-card__info__post-title')
        for link in links:
            url = link.get('href')
            if url not in self.urls:
                return url
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()
        for seed_url in seed_urls:
            response = make_request(seed_url, self.config)
            if not response.ok:
                continue
            article_bs = BeautifulSoup(response.text, "lxml")
            extracted_url = self._extract_url(article_bs)
            while extracted_url:
                if len(self.urls) == self.config.get_num_articles():
                    break
                self.urls.append(extracted_url)
                extracted_url = self._extract_url(article_bs)
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
        self.article = Article(self.full_url, self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        art = []
        all_pars = article_soup.find_all('div', class_='first-content')
        for pargraphs in all_pars:
            all_paragraphs = pargraphs.find_all('p')
            for parag in all_paragraphs:
                if parag.text:
                    art.append(parag.text)
        self.article.text = '/n'.join(art).strip()

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
        response = make_request(self.full_url, self.config)
        if response.ok:
            article_bs = BeautifulSoup(response.text, 'lxml')
            self._fill_article_with_text(article_bs)
        return self.article


def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    base_path.mkdir(parents=True, exist_ok=True)
    for file in base_path.iterdir():
        file.unlink(missing_ok=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=constants.CRAWLER_CONFIG_PATH)
    prepare_environment(base_path=constants.ASSETS_PATH)
    crawler = Crawler(config)
    crawler.find_articles()
    for i, url in enumerate(crawler.urls):
        parser = HTMLParser(full_url=url, article_id=i + 1, config=config)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)


if __name__ == "__main__":
    main()
