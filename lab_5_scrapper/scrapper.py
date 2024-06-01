"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
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
    The seed-url is not appropriate.
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
        self.config = self._extract_config_content()
        self._validate_config_content()
        self._num_articles = self.config.total_articles
        self._seed_urls = self.get_seed_urls()
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
        config = json.load(self.path_to_config.open())
        config_dto = ConfigDTO(**config)

        return config_dto

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not isinstance(self.config.seed_urls, list) or not all(
            seed.startswith('https://xn--80ady2a0c.xn--p1ai/calendar/')
            for seed in self.config.seed_urls
        ):
            raise IncorrectSeedURLError
        if (not isinstance(self.config.total_articles, int)
                or self.config.total_articles < 1):
            raise IncorrectNumberOfArticlesError
        if self.config.total_articles < 1 or self.config.total_articles > 150:
            raise NumberOfArticlesOutOfRangeError
        if not isinstance(self.config.headers, dict):
            raise IncorrectHeadersError
        if not isinstance(self.config.encoding, str):
            raise IncorrectEncodingError
        if (not isinstance(self.config.timeout, int) or
            self.config.timeout < 1 or self.config.timeout > 60):
            raise IncorrectTimeoutError
        if not isinstance(self.config.headless_mode, bool) \
                or not isinstance(self.config.should_verify_certificate, bool):
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
    return requests.get(url=url,
                        headers=config.get_headers(),
                        timeout=config.get_timeout()
                        # verify = config.get_verify_certificate()
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
        soup = article_bs
        divs_news_from_site = soup.find_all('div', class_="news")
        for div in divs_news_from_site:
            div.find_next('a').select_one("div").decompose()
            url_page_from_site = str(div.find_next('a'))[9:-6]
            div.find_next('a').decompose()
            if str(div) == '<div class="news"></div>':
                div.decompose()
            break


        return url_page_from_site

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

                article_bs = BeautifulSoup(response.text, "lxml")
                extracted = []
                for _ in range(self.config.get_num_articles()):
                    extracted.append(self._extract_url(article_bs))
                for url in extracted:
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
        self._config = config
        self.article = Article(url=full_url, article_id=article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Find text of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.text = article_soup.get_text()[
                            article_soup.get_text().find("печати") + 6:article_soup.get_text().find(
                                "Если Вы заметили ошибку в тексте")].replace(
            "\n", " ").replace(".", "\n.").replace(" ", ' ')

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.author.append('NOT FOUND')

        self.article.title = article_soup.find_all('h1')[0].text

        date = str(article_soup.find_all("div", {"class": "sh_tb_0"})[0])
        date = date[date.find('>')+1:date.find(' ·'):1]
        self.article.date = self.unify_date_format(date)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        if date_str[0:1] == 'П':
            return datetime.datetime.strptime('2000-01-01 01:01:01', '%Y-%m-%d %H:%M:%S')

        mounts = {'января,': '01', 'февраля,': '02', 'марта,': '03',
                  'апреля,': '04', 'мая,': '05'}
        good_data_string = date_str.split()
        good_data_string[1] = mounts[good_data_string[1]] + '-'
        good_data_string[2] = good_data_string[0] + ' ' + good_data_string[2] + ':00'
        good_data_string[0] ='2024-'
        return datetime.datetime.strptime(''.join(good_data_string), '%Y-%m-%d %H:%M:%S')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parse each article.

        Returns:
            Union[Article, bool, list]: Article instance
        """
        response = make_request(url=self.full_url, config=self._config)
        if not response.ok:
            return False
        article_bs = BeautifulSoup(response.text, features="lxml")

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
    base_path.mkdir()


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    crawler = Crawler(config)
    prepare_environment(ASSETS_PATH)

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
