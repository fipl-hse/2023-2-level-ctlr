"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import requests
import shutil
import time
from bs4 import BeautifulSoup
from core_utils.article import io
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH
from core_utils.article.article import Article
from random import randrange
from typing import Pattern, Union


class IncorrectSeedURLError(Exception):
    """
    Seed URLs do not belong to the website being scrapped.
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    The number of articles to be collected is not positive or is greater than 150.
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    The number of articles to be collected is not an integer number.
    """


class IncorrectHeadersError(Exception):
    """
    Headers are not presented as a dictionary.
    """


class IncorrectEncodingError(Exception):
    """
    Encoding is not specified as a string.
    """


class IncorrectTimeoutError(Exception):
    """
    The timeout is not a positive integer number or is greater than 60.
    """


class IncorrectVerifyError(Exception):
    """
    The verify certificate value is not boolean.
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

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config) as config_file:
            config = json.load(config_file)
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not all(seed.startswith('https://www.fontanka.ru/') for seed in self.config.seed_urls):
            raise IncorrectSeedURLError
        if self.config.total_articles < 1 or self.config.total_articles > 150:
            raise NumberOfArticlesOutOfRangeError
        if not isinstance(self.config.total_articles, int):
            raise IncorrectNumberOfArticlesError
        if not isinstance(self.config.headers, dict):
            raise IncorrectHeadersError
        if not isinstance(self.config.encoding, str):
            raise IncorrectEncodingError
        if self.config.timeout < 1 or self.config.timeout > 60:
            raise IncorrectTimeoutError
        if not isinstance(self.config.headless_mode, bool):
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
    verify = config.get_verify_certificate()
    headers = config.get_headers()
    timeout = config.get_timeout()
    time.sleep(randrange(1, 10))
    return requests.get(url=url, verify=verify, headers=headers, timeout=timeout)


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
        articles = article_bs.find_all('a', class_='IFcb')
        url = ''
        for article in articles:
            url = 'https://www.fontanka.ru' + article.get('href')
            if url not in self.urls:
                break
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        goal = self.config.get_num_articles()
        while len(self.urls) < goal:
            for seed in self.get_search_urls():
                response = make_request(seed, self.config)
                if not response.ok:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                url = self._extract_url(soup)
                if url:
                    self.urls.append(url)

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
        self.article = Article(url=full_url, article_id=article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        content = article_soup.find(itemprop='ArticleBody').find_all('p')
        self.article.text = '\n'.join(content)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.title = article_soup.find('h1').text

        topics = article_soup.find(class_='ANf9').find_all('a')
        self.article.topics = [topic.text for topic in topics]

        author = [a.text for a in article_soup.find_all('p', itemprop='name')]
        if not author:
            author = ['NOT FOUND']
        self.article.author = author

        date = article_soup.find(itemprop='datePublished').text
        self.article.date = self.unify_date_format(date)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        # 1 мая 2024, 14:49
        date = date_str.split()
        month = {'января': '01',
                 'февраля': '02',
                 'марта': '03',
                 'апреля': '04',
                 'мая': '05',
                 'июня': '06',
                 'июля': '07',
                 'августа': '08',
                 'сентября': '09',
                 'октября': '10',
                 'ноября': '11',
                 'декабря': '12'
                 }
        date[1] = month[date[1]]
        return datetime.datetime.strptime(''.join(date), '%d %m %Y, %H:%M')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(url=self.full_url, config=self.config)
        if response.ok:
            soup = BeautifulSoup(response.text)
            self._fill_article_with_text(soup)
            self._fill_article_with_meta_information(soup)
        return self.article


def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    if not base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    crawler = Crawler(config)
    prepare_environment(ASSETS_PATH)

    crawler.find_articles()
    for i, url in enumerate(crawler.urls):
        parser = HTMLParser(full_url=url, article_id=i + 1, config=config)
        article = parser.parse()
        io.to_raw(article)
        io.to_meta(article)


if __name__ == "__main__":
    main()
