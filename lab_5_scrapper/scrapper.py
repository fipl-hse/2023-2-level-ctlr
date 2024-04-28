"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
from typing import Pattern, Union
from core_utils.config_dto import ConfigDTO
import json
import re
from bs4 import BeautifulSoup
from pathlib import Path
import shutil
import requests
import datetime
from core_utils.article.article import Article
from core_utils.article.io import to_raw, to_meta
from core_utils.constants import CRAWLER_CONFIG_PATH, ASSETS_PATH


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
        Verify certificate value must either be True or False.
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

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        file_config = json.load(open(self.path_to_config))
        config = ConfigDTO(**file_config)
        return config

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = json.load(open(self.path_to_config))
        pattern = 'https?://(www.)?'

        if not(isinstance(config['seed_urls'], list) and
               all(re.match(pattern, x) for x in config['seed_urls'])):
            raise IncorrectSeedURLError

        if not isinstance(config['total_articles_to_find_and_parse'], int)\
                or config['total_articles_to_find_and_parse'] <= 0:
            raise IncorrectNumberOfArticlesError

        if config['total_articles_to_find_and_parse'] > 150:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config['headers'], dict):
            raise IncorrectHeadersError

        if not isinstance(config['encoding'], str):
            raise IncorrectEncodingError

        if not (isinstance(config['timeout'], int) and 0 < config['timeout'] < 60):
            raise IncorrectTimeoutError

        if not isinstance(config['should_verify_certificate'], bool):
            raise IncorrectVerifyError

        if not isinstance(config['headless_mode'], bool):
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
        return self._config.headers

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
    reqs = requests.get(
        url=url,
        headers=config.get_headers(),
        timeout=config.get_timeout(),
        verify=config.get_verify_certificate())
    return reqs


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
        self.urls = []
        self.config = config
        self.url = 'https://newsorel.ru/'

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Find and retrieve url from HTML.

        Args:
            article_bs (bs4.BeautifulSoup): BeautifulSoup instance

        Returns:
            str: Url from HTML
        """
        all_div = article_bs.find('div', class_="big-news-list-block")
        h2_tags = all_div.find_all('h2')
        for h2 in h2_tags:
            link = h2.find('a')
            href = link.get('href')
            url = self.url + href
            if url not in self.urls:
                return url

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()

        while len(self.urls) < self.config.get_num_articles():
            for seed_url in seed_urls:
                response = make_request(seed_url, self.config)
                if not response.ok:
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                urls = self._extract_url(soup)
                self.urls.append(urls)
                if len(self.urls) >= self.config.get_num_articles():
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

        all_body = article_soup.find('span', itemprop='articleBody')

        texts = []
        if all_body:
            all_ps_style = all_body.find_all('p', style="text-align: justify;")
            all_ps = all_body.find_all('p')
            texts = []
            for p_bs_style in all_ps_style:
                texts.append(p_bs_style.text)
            for p_bs in all_ps:
                texts.append(p_bs.text)
        self.article.text = '\n'.join(texts)

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        header = article_soup.find('h1')
        if header:
            self.article.title = header.text

        author = article_soup.find('span', itemprop="name")
        if author:
            self.article.author = [author.text]
        else:
            self.article.author = ['NOT FOUND']

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
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(base_path=ASSETS_PATH)

    crawler = Crawler(config=config)
    crawler.find_articles()
    for index, url in enumerate(crawler.urls):
        parser = HTMLParser(full_url=url, article_id=index+1, config=config)
        article = parser.parse()
        if isinstance(article, Article):
            to_raw(article)
            to_meta(article)


if __name__ == "__main__":
    main()
