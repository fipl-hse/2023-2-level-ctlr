"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
import re
import shutil
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH


class IncorrectSeedURLError(Exception):
    """
    Seed URL does not match standard pattern.
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Total number of articles to parse is not integer.
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Total number of articles is out of range from 1 to 150.
    """


class IncorrectHeadersError(Exception):
    """
    Headers are not in a form of dictionary.
    """


class IncorrectEncodingError(Exception):
    """
    encoding must be specified as a string.
    """


class IncorrectTimeoutError(Exception):
    """
    timeout value must be a positive integer less than 60.
    """


class IncorrectVerifyError(Exception):
    """
    verify certificate value must either be True or False.
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
        self._configuration = self._extract_config_content()
        self._seed_urls = self._configuration.seed_urls
        self._num_articles = self._configuration.total_articles
        self._headers = self._configuration.headers
        self._encoding = self._configuration.encoding
        self._timeout = self._configuration.timeout
        self._should_verify_certificate = self._configuration.should_verify_certificate
        self._headless_mode = self._configuration.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        with open(file=self.path_to_config, mode='r', encoding='utf-8') as file:
            config = json.load(file)
        return ConfigDTO(**config)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        pattern = "https?://(www.)?"

        if not isinstance(config['seed_urls'], list):
            raise IncorrectSeedURLError
        for seed_url in config['seed_urls']:
            if not re.match(pattern, seed_url):
                raise IncorrectSeedURLError

        if (not isinstance(config['total_articles_to_find_and_parse'], int)
                or config['total_articles_to_find_and_parse'] <= 0):
            raise IncorrectNumberOfArticlesError

        if not 0 < config['total_articles_to_find_and_parse'] < 151:
            raise NumberOfArticlesOutOfRangeError

        if not isinstance(config['headers'], dict):
            raise IncorrectHeadersError

        if not isinstance(config['encoding'], str):
            raise IncorrectEncodingError

        if not isinstance(config['timeout'], int) or not 0 < config['timeout'] < 60:
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
        return self._configuration.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self._configuration.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self._configuration.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self._configuration.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self._configuration.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self._configuration.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self._configuration.headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Deliver a response from a request with given configuration.

    Args:
        url (str): Site url
        config (Config): Configuration

    Returns:
        requests.models.Response: A response from a request
    """
    response = requests.get(url=url, timeout=config.get_timeout(),
                            headers=config.get_headers(), verify=config.get_verify_certificate())
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
        url = article_bs.get('href')
        return str(url) if url else ''

    def find_articles(self) -> None:
        """
        Find articles.
        """
        for url in self.get_search_urls():
            response = make_request(url, self.config)
            if not response.ok:
                continue

            article_bs = BeautifulSoup(response.text, 'html.parser')
            for h3 in article_bs.find_all("h3", {'class': "item-title"}):
                for tag in h3.select('a'):
                    if len(self.urls) == self.config.get_num_articles():
                        break

                    url = self._extract_url(tag)
                    if url != '' and url not in self.urls:
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
        self.article = Article(full_url, article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        all_body = article_soup.find('div', class_='wp-content')

        texts = []
        if all_body:
            paragraphs = all_body.find_all('p')
            for p in paragraphs:
                if p.find('strong'):
                    break
                texts.append(p.text)
        self.article.text = '\n'.join(texts).replace(' ', ' ')

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        title = article_soup.find("h1", class_="title")
        self.article.title = title.text
        date = article_soup.find('span', class_='date').text
        self.article.date = self.unify_date_format(date)

        author = ''
        after_text = False
        author_list = []
        elements = article_soup.find_all('strong')
        if len(elements) > 1:
            for el in elements:
                el_text = el.text
                if 'Текст' in el_text:
                    after_text = True
                if after_text:
                    author_list.append(el_text.strip())
            author = ' '.join(author_list)

        else:
            author = elements[0].text
        if ' :' in author:
            author = author[8:].strip().replace('  ', ' ')
            al = author.split()
            author = al[-1]
        else:
            author = author[7:]
        if not author:
            author = 'NOT FOUND'

        self.article.author = [author]
        print(self.article.author)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        converter = {'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04', 'мая': '05',
                     'июня': '06', 'июля': '07', 'августа': '08', 'сентября': '09',
                     'октября': '10', 'ноября': '11', 'декабря': '12'}
        date = date_str.split()
        month = converter[date[1]]
        date[1] = month
        return datetime.datetime.strptime(" ".join(date), '%d %m %Y')

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
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(config=config)
    crawler.find_articles()
    for i, url in enumerate(crawler.urls):
        parser = HTMLParser(full_url=url, article_id=i + 1, config=config)
        text = parser.parse()
        if isinstance(text, Article):
            to_raw(text)
            to_meta(text)

if __name__ == "__main__":
    main()
