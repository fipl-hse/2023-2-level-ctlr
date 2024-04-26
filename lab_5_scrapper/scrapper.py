"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import pathlib
from typing import Pattern, Union
import requests
import json
import re
import datetime
import shutil
from bs4 import BeautifulSoup
from core_utils.article.article import Article
from core_utils.config_dto import ConfigDTO
from core_utils.article.io import to_raw, to_meta
from core_utils.constants import CRAWLER_CONFIG_PATH, ASSETS_PATH


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
        with open(self.path_to_config) as file:
            data = json.load(file)
        return ConfigDTO(**data)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        config = self._extract_config_content()
        pattern = "https?://www.gazetavechorka.ru?"
        if not isinstance(config.seed_urls, list) or \
                not all(re.match(pattern, x) for x in config.seed_urls):
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

        if not isinstance(config.timeout, int) or 0 >= config.timeout or config.timeout >= 60:
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
        container_div = article_bs.find('div', class_='col-lg-9 col-md-12')
        for link in container_div.find_all('a', href=True):
            if link.get('href').startswith('/news/202'):
                href = 'https://www.gazetavechorka.ru' + link.get('href')
                if href and href not in self.urls:
                    return href

    def find_articles(self) -> None:
        """
        Find articles.
        """
        seed_urls = self.get_search_urls()
        necessary_len = self.config.get_num_articles()

        while len(self.urls) != necessary_len:
            for url in seed_urls:
                response = make_request(url, self.config)

                if response.ok:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    extracted = self._extract_url(soup)

                    while extracted:
                        self.urls.append(extracted)
                        if len(self.urls) == necessary_len:
                            break
                        extracted = self._extract_url(soup)

                    if not extracted:
                        continue

                if len(self.urls) == necessary_len:
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
        div = article_soup.find('div', class_='col-lg-9 col-md-12')
        div_news = div.find('div', class_='news-content')

        all_ps = div_news.find_all('p')
        tag_to_remove = 'em'
        tag = article_soup.find(tag_to_remove)
        if tag:
            tag.decompose()

        texts = []
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
            self.article.title = header

        self.article.author = 'NOT FOUND'

        element = article_soup.find('ul', class_='list-unstyled list-inline').find('li', class_='list-inline-item')
        date = element.get_text().strip().split(', ')[1]
        self.article.date = date

        meta_tag = article_soup.find('meta', attrs={'meta': 'keywords'})
        topics = []
        if meta_tag:
            topics = meta_tag['content'].split(', ')
        self.article.topics = topics



    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unify date format.

        Args:
            date_str (str): Date in text format

        Returns:
            datetime.datetime: Datetime object
        """
        return datetime.datetime.strptime(date_str, '%d.%m.%Y %H:%M')

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
    if not base_path.exists():
        base_path.mkdir(parents=True)
    else:
        shutil.rmtree(base_path)
        base_path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(base_path=ASSETS_PATH)

    crawler = Crawler(config=config)
    crawler.find_articles()
    urls = crawler.urls
    for index, url in enumerate(urls):
        parser = HTMLParser(full_url=url, article_id=index, config=config)
        article = parser.parse()
        to_raw(article)
        to_meta(article)



if __name__ == "__main__":
    main()
