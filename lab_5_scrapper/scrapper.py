"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import re
from random import randrange
from time import sleep
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH


class IncorrectSeedURLError(Exception):
    """
    All the seed URLs must belong to the website being scrapped.
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    The number of articles to be collected must be a positive number less than 150.
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    The number of articles to be collected must be a positive integer number.
    """


class IncorrectHeadersError(Exception):
    """
    Headers must be presented as a dictionary.
    """


class IncorrectEncodingError(Exception):
    """
    Encoding must be specified as a string.
    """


class IncorrectTimeoutError(Exception):
    """
    The timeout must be a positive integer number less than the set limit.
    """


class IncorrectVerifyError(Exception):
    """
    The verify certificate value must be boolean.
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
        with open(self.path_to_config, encoding='utf-8') as file:
            config = json.load(file)
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()

        if not (isinstance(config.seed_urls, list)
                and all(re.match(r"https?://(www)?\.myslo.ru+", seed_url)
                        for seed_url in config.seed_urls
                        )
                ):
            raise IncorrectSeedURLError

        if not isinstance(config.total_articles, int) or config.total_articles <= 0:
            raise IncorrectNumberOfArticlesError

        if config.total_articles > 150:
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
        headers=config.get_headers(),
        timeout=config.get_timeout(),
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
        self.url_pattern = 'https://myslo.ru/club/blog/zvere-moe'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        link = article_bs.find('a', attrs={'class': 'figcaption promo-link'})
        url = str(self.url_pattern + link.get('href'))
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        urls = []
        while len(urls) < self.config.get_num_articles():
            for url in self.get_search_urls():
                response = make_request(url, self.config)
                if not response.ok:
                    continue
                article_bs = BeautifulSoup(response.text, 'lxml')
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
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        description = article_soup.find('meta', attrs={'name': 'description'}).text
        all_txt = article_soup.find('div', attrs={'class': 'detail-text-div'}).text
        self.article.text = str(description + all_txt)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.title = article_soup.find('meta', property='og:title').attrs['content']

        author = article_soup.find('meta', attrs={'itemprop': 'author'}).attrs['content']
        if not author or len(author) == 0:
            self.article.author.append('NOT FOUND')
        else:
            self.article.author.append(author)

        date = article_soup.find('meta', attrs={'itemprop': 'dateModified'}).attrs['content']
        if date:
            self.article.date = self.unify_date_format(date)

        topics = article_soup.find('div', class_='article-tag-tags').find_all('a')
        for topic in topics:
            self.article.topics.append(topic.text)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        if 'MSK' in date_str:
            date_str = date_str.replace('MSK', ' ')
        if '+00:00' in date_str:
            date_str = date_str.replace('+00:00', '')
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

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
    base_path.mkdir(parents=True, exist_ok=True)
    for file in base_path.iterdir():
        file.unlink(missing_ok=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)

    crawler = Crawler(config)
    crawler.find_articles()

    for index, url in enumerate(crawler.urls, 1):
        parser = HTMLParser(url, index, config)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)
        print('Done')


if __name__ == "__main__":
    main()
