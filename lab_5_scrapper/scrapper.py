"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import re
import shutil
from random import randrange
from time import sleep
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import (ASSETS_PATH, CRAWLER_CONFIG_PATH, NUM_ARTICLES_UPPER_LIMIT,
                                  TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT)


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
        self._config = self._extract_config_content()

        self._seed_urls = self._config.seed_urls
        self._num_articles = self._config.total_articles
        self._headers = self._config.headers
        self._encoding = self._config.encoding
        self._timeout = self._config.timeout
        self._should_verify_certificate = self._config.should_verify_certificate
        self._headless_mode = self._config.headless_mode

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
        pattern = "https?://www.myslo.ru?"
        if not isinstance(config.seed_urls, list) or \
                not all(re.match(pattern, x) for x in config.seed_urls):
            raise IncorrectSeedURLError

        num = config.total_articles

        if not isinstance(num, int) or num <= 0:
            raise IncorrectNumberOfArticlesError

        if num > NUM_ARTICLES_UPPER_LIMIT:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(config.encoding, str):
            raise IncorrectEncodingError

        if not isinstance(config.timeout, int) \
                or TIMEOUT_LOWER_LIMIT >= config.timeout \
                or config.timeout >= TIMEOUT_UPPER_LIMIT:
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
        self._config = config
        self.urls = []
        self.url_pattern = 'https://www.myslo.ru'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        links = article_bs.find_all(class_="h3")

        for link in links:
            url = self.url_pattern + str(link.find('a').get('href'))
            if url not in self.urls:
                break
        else:
            url = ''

        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        urls = []
        while len(urls) < self._config.get_num_articles():
            for url in self.get_search_urls():
                response = make_request(url, self._config)
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
        return self._config.get_seed_urls()


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
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        title = article_soup.find("h1", class_="h1").text
        title_strip = title.replace('\xa0', ' ')
        title_strip = title_strip.replace('«', '')
        title_strip = title_strip.replace('»', '')

        texts = []
        text_paragraphs = article_soup.find_all("p")
        for paragraph in text_paragraphs:
            texts.append(paragraph.text)
        texts1 = ''.join(texts)
        text_strip = texts1.replace('\xa0', ' ')
        if title_strip:
            self.article.text = title_strip + "\n" + text_strip
        else:
            self.article.text = text_strip

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        title = article_soup.find("h1", class_="h1").text  # В&#160;Туле один водитель &#171;прокатил&#187; другого на&#160;капоте - Новости Тулы и области. Криминал
        # title_strip = title.replace("&nbsp;", '').replace('&#160;', '').replace('&#32;', '').replace('&#x2423;', '')
        # title_strip = title_strip.replace("&#xA0;", '').replace('&#x20;', '').replace('&#x2420;', '')
        # title_strip = title_strip.replace('&#9251;', '').replace('&#9248;', '')
        # title_strip = title_strip.replace(r'&quot;', '"').replace(r'\\', '')
        print(repr(title))
        title_1 = title.split("&#xA0;")
        title_2 = re.split('\xa0', title)
        print(repr(title_1), repr(title_2))
        if title:
            self.article.title = title[0]

        author_element = article_soup.find(class_="authorDetails")
        author = author_element.find("a")
        if author is None or author.get_text(strip=True) == '':
            self.article.author.append("NOT FOUND")
        else:
            self.article.author.append(author.get_text(strip=True))

        date_str = article_soup.find(class_='authorDetails')
        contents = []
        for i in date_str.find_all('meta'):
            if i.has_attr('content'):
                contents.append(i['content'])
        self.article.date = self.unify_date_format(contents[-2])

        tags = article_soup.find(class_='block-tegs-text')
        if not tags:
            self.article.topics.append('NOT FOUND')
        else:
            for tag in tags:
                self.article.topics.append(tag.text)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        date_str = date_str.replace('T', ' ')
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(self.full_url, self._config)
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


if __name__ == "__main__":
    main()
