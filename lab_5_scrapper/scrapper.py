"""
Crawler implementation.
"""
import datetime
import json
import os.path
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
import re
import shutil

from bs4 import BeautifulSoup
import requests
from typing import Pattern, Union

from core_utils import constants
from core_utils.article.article import Article
from core_utils.article.io import to_raw
from core_utils.config_dto import ConfigDTO


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
        self.config = self._extract_config_content()
        self._seed_urls = self.config.seed_urls
        self._headers = self.config.headers
        self._num_articles = self.config.total_articles
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
        with open(file=self.path_to_config, mode="r", encoding="utf-8") as f:
            conf = json.load(f)
            return ConfigDTO(seed_urls=conf["seed_urls"], headers=conf['headers'],
                             total_articles_to_find_and_parse=conf['total_articles_to_find_and_parse'],
                             encoding=conf['encoding'], timeout=conf['timeout'],
                             should_verify_certificate=conf['should_verify_certificate'],
                             headless_mode=conf['headless_mode'])

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        with open(file=self.path_to_config, mode="r", encoding="utf-8") as f:
            conf = json.load(f)
        if not (isinstance(conf['seed_urls'], list)
                and all(re.match(r"https?://(www.)?", seed_url) for seed_url in conf['seed_urls'])):
            raise IncorrectSeedURLError
        number = conf['total_articles_to_find_and_parse']
        if not isinstance(number, int) or number <= 0:
            raise IncorrectNumberOfArticlesError
        if not 1 <= number <= 150:
            raise NumberOfArticlesOutOfRangeError
        if not isinstance(conf['headers'], dict):
            raise IncorrectHeadersError
        if not isinstance(conf['encoding'], str):
            raise IncorrectEncodingError
        if not (isinstance(conf['timeout'], int) and 0 < conf['timeout'] < 60):
            raise IncorrectTimeoutError
        if not isinstance(conf['should_verify_certificate'], bool) or not isinstance(conf['headless_mode'], bool):
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
    return requests.get(url=url, timeout=config.get_timeout(), headers=config.get_headers(),
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
        self.url_pattern = self.config.get_seed_urls()[0].split('/news')[0]

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        url = ''
        urls = article_bs.findAll('a', class_='entry-header')
        for el in urls:
            url = el.get('href')
            if url.split('/')[2] == 'servernews.ru':
                continue
            if url not in self.urls:
                break
        url = self.url_pattern + url
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seeds = self.get_search_urls()
        for seed in seeds:
            response = make_request(seed, self.config)
            if not response.ok:
                continue
            article_bs = BeautifulSoup(response.text, 'html.parser')
            urls = []
            for i in range(25):
                urls.append(self._extract_url(article_bs))
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
        headline = article_soup.find('h1', itemprop='headline')
        text = f'{headline.string}'
        texts = article_soup.findAll('p')
        for el in texts:
            if not el.string:
                continue
            text += f'{texts}'
        self.article.text = text

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
            article_bs = BeautifulSoup(response.text, 'html.parser')
            self._fill_article_with_text(article_bs)
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
    prepare_environment(base_path=constants.ASSETS_PATH)
    configuration = Config(path_to_config=constants.CRAWLER_CONFIG_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()
    urls = crawler.urls
    for i, url in enumerate(urls):
        parser = HTMLParser(full_url=url, article_id=i+1, config=configuration)
        article = parser.parse()
        to_raw(article)
    print('ok')


if __name__ == "__main__":
    main()
