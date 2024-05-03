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
    Seed URL does not match standard pattern.
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
    Certificate value must be a bool type.
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
        self.config_dto = self._extract_config_content()
        self._validate_config_content()

        self._seed_urls = self.config_dto.seed_urls
        self._num_articles = self.config_dto.total_articles
        self._headers = self.config_dto.headers
        self._encoding = self.config_dto.encoding
        self._timeout = self.config_dto.timeout
        self._should_verify_certificate = self.config_dto.should_verify_certificate
        self._headless_mode = self.config_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not (
            isinstance(self.config_dto.seed_urls, list)
            and all(
                re.match(r"https?://(www.)?securitylab\.ru/news", seed_url)
                for seed_url in self.config_dto.seed_urls
                    )
                ):
            raise IncorrectSeedURLError

        if (
            not isinstance(self.config_dto.total_articles, int)
            or self.config_dto.total_articles <= 0
        ):
            raise IncorrectNumberOfArticlesError

        if (
            self.config_dto.total_articles > 150
        ):
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(self.config_dto.headers, dict):
            raise IncorrectHeadersError

        if not isinstance(self.config_dto.encoding, str):
            raise IncorrectEncodingError

        if (not isinstance(self.config_dto.timeout , int)
            or not 0 <= self.config_dto.timeout < 60
        ):
            raise IncorrectTimeoutError

        if (
            not isinstance(self.config_dto.should_verify_certificate, bool)
            or not isinstance(self.config_dto.headless_mode, bool)
        ):
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
    sleep(random.randint(1, 6))

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

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        url = ""
        links = article_bs.find_all('a')
        for link in links:
            link = link.get('href')
            if (link and link.startswith('/news/')
                and link.endswith('php')):
                url = 'https://www.securitylab.ru' + link
                if url not in self.urls:
                    return url
        return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        for url in self.get_search_urls():
            response = make_request(url, self.config)

            if not response.ok:
                continue
            soup = BeautifulSoup(response.text, 'lxml')
            extr = self._extract_url(soup)
            while extr and len(self.urls) < self.config.get_num_articles():
                self.urls.append(extr)
                extr = self._extract_url(soup)

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
        self.article_id = article_id + 1
        self.config = config
        self.article = Article(self.full_url, self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        description = article_soup.find('p').text
        text = article_soup.find('div', itemprop='description').stripped_strings

        self.article.text = description.strip() + "\n" + '\n'.join(text)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        title = article_soup.find('title').string.strip()
        self.article.title = title

        author = article_soup.find('div', itemprop='author').text
        if author:
            self.article.author.append(author)

        date = article_soup.find('time', itemprop='datePublished').string
        if date:
            date_str = date[:-6].replace('T', ' ')
            self.article.date = self.unify_date_format(str(date_str))

        keyword_class = article_soup.find_all(class_ ='tag tag-outline-primary')
        if keyword_class:
            self.article.topics = []
            for key in keyword_class:
                if key not in self.article.topics:
                    keyword = key.string.strip()
                    self.article.topics.append(keyword)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        formatted_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return formatted_date

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
    prepare_environment(constants.ASSETS_PATH)
    configuration = Config(constants.CRAWLER_CONFIG_PATH)
    crawler = Crawler(configuration)
    crawler.find_articles()

    for i, url in enumerate(crawler.urls):
        parser = HTMLParser(url, i, configuration)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)

class CrawlerRecursive(Crawler):
    """
    The Crawler in a recursive manner.

    """

    def __init__(self, configuration: Config) -> None:
        '''
        Recursive Crawler implementation.
        '''

        super().__init__(configuration)
        self.start_url = self.config.get_seed_urls()[0]
        self.crawling_path = pathlib.Path('tmp/crawled_urls.json')
        self.parsing_path = pathlib.Path('tmp/parsed_urls.json')
        self.all_urls = [self.start_url]
        self.domain = 'https://www.securitylab.ru'
        self.num_of_urls = 0
        self.parsed_urls = []

    def save_crawled_urls(self) -> None:
        '''
        Save the json information about crawling
        '''
        json_info = {'all_urls': self.all_urls,
                     'article_urls': self.urls,
                     'num_of_crawled_urls': self.num_of_urls}

        with open (self.crawling_path, 'w', encoding='utf-8') as f:
            json.dump(json_info, f, indent=3)

    def find_articles(self) -> None:
        """
        Find articles using RecursiveCrawler
        """
        if len(self.urls) < self.config.get_num_articles:
            if len(self.all_urls) != 0:
                url = self.all_urls[self.num_of_urls]
            url = self.start_url

            response = make_request(url, self.config)
            if not response.ok:
                return

            soup = BeautifulSoup(response.text, 'lxml')
            links = soup.find_all('a')
            for link in links:
                link = link.get('href')
                if link and (link.startswith('/') or link.startswith('page')):
                    if (self.domain + link) not in self.all_urls:
                        sleep(random.randint(1, 5))
                        if link.startswith('page'):
                            self.all_urls.append(self.domain + '/news/' + link)
                        else:
                            self.all_urls.append(self.domain + link)

                        self.save_crawled_urls()
                        extr = self._extract_url(soup)
                        if (extr and extr not in self.urls
                            and len(self.urls) < self.config.get_num_articles):
                            self.urls.append(extr)
                            self.save_crawled_urls()

            if len(self.urls) < self.config.get_num_articles:
                self.num_of_urls += 1
            self.find_articles()


def recursive_main() -> None:
    """
    Entrypoint for scrapper module.
    """
    configuration = Config(constants.CRAWLER_CONFIG_PATH)
    crawler = CrawlerRecursive(configuration)

    if crawler.crawling_path.exists():
        with open(crawler.crawling_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            crawler.all_urls = data['all_urls']
            crawler.urls = data['article_urls']
            crawler.num_of_urls = data['num_of_crawled_urls']
            crawler.save_crawled_urls
    if crawler.parsing_path.exists():
        with open(crawler.parsing_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            crawler.parsed_urls = data['parsed_urls']
    else:
        prepare_environment(constants.ASSETS_PATH)

    crawler.find_articles()

    for i, url in enumerate(crawler.urls):
        if url not in crawler.parsed_urls:
            parser = HTMLParser(url, i, configuration)
            article = parser.parse()
            if isinstance(article, Article):
                to_raw(article)
                to_meta(article)

if __name__ == "__main__":
    main()
