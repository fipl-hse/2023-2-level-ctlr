"""
Crawler implementation.
"""
# pylint: disable=too-many-arguments, too-many-instance-attributes, unused-import, undefined-variable
import datetime
import json
import pathlib
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH

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
        self.CRAWLER_CONFIG_PATH = path_to_config
        self.config_DTO = self._extract_config_content()
        self._validate_config_content()
        prepare_environment(ASSETS_PATH)

    def _extract_config_content(self) -> ConfigDTO:
        """
        Get config values.

        Returns:
            ConfigDTO: Config values
        """
        config = json.load(self.CRAWLER_CONFIG_PATH.open())
        config_DTO = ConfigDTO(**config)

        return config_DTO

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters are not corrupt.
        """
        if not all(seed.startswith('https://xn--80ady2a0c.xn--p1ai/calendar/2024/') for seed in self.config_DTO.seed_urls):
            raise Exception('IncorrectSeedURLError')
        if self.config_DTO.total_articles < 1 or self.config_DTO.total_articles > 150:
            raise Exception('NumberOfArticlesOutOfRangeError')
        if not isinstance(self.config_DTO.total_articles, int):
            raise Exception('IncorrectNumberOfArticlesError')
        if not isinstance(self.config_DTO.headers, dict):
            raise Exception('IncorrectHeadersError')
        if not isinstance(self.config_DTO.encoding, str):
            raise Exception('IncorrectEncodingError')
        if self.config_DTO.timeout < 1 or self.config_DTO.timeout > 60:
            raise Exception('IncorrectTimeoutError')
        if not isinstance(self.config_DTO.headless_mode, bool):
            raise Exception('IncorrectVerifyError')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls.

        Returns:
            list[str]: Seed urls
        """

        return self.config_DTO.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape.

        Returns:
            int: Total number of articles to scrape
        """
        return self.config_DTO.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting.

        Returns:
            dict[str, str]: Headers
        """
        return self.config_DTO.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing.

        Returns:
            str: Encoding
        """
        return self.config_DTO.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response.

        Returns:
            int: Number of seconds to wait for response
        """
        return self.config_DTO.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate.

        Returns:
            bool: Whether to verify certificate or not
        """
        return self.config_DTO.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode.

        Returns:
            bool: Whether to use headless mode or not
        """
        return self.config_DTO.headless_mode


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
                        #verify = config.get_verify_certificate()
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
                extracted = self._extract_url(article_bs)
                self.urls.append(extracted)

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
        self.article.text = article_soup.get_text()[article_soup.get_text().find("печати") + 6:article_soup.get_text().find(
        "Если Вы заметили ошибку в тексте, выделите её и нажмите Ctrl+Enter, чтобы отослать информацию редактору. Спасибо!")].replace(
        "\n", " ").replace(".", "\n.").replace(" ", ' ')

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Find meta information of article.

        Args:
            article_soup (bs4.BeautifulSoup): BeautifulSoup instance
        """
        self.article.author.append('NOT FOUND')

        self.article.topics.append(article_soup.find_all('h1')[0].text)

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
        response = make_request(url=self.full_url, config=self.config)
        if not response.ok:
            return False
        егоarticle_bs = BeautifulSoup(response.text, features="lxml")

        self._fill_article_with_text(егоarticle_bs)
        self._fill_article_with_meta_information(егоarticle_bs)

        return self.article

def prepare_environment(base_path: Union[pathlib.Path, str]) -> None:
    """
    Create ASSETS_PATH folder if no created and remove existing folder.

    Args:
        base_path (Union[pathlib.Path, str]): Path where articles stores
    """
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(exist_ok=True, parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module.
    """
    config = Config(path_to_config=CRAWLER_CONFIG_PATH)
    crawler = Crawler(config)
    prepare_environment(ASSETS_PATH)

    crawler.find_articles()
    i = 1
    for url in crawler.urls:
        parser = HTMLParser(full_url=url, article_id=i, config=config)
        article = parser.parse()
        if isinstance(article, Article):
            io.to_raw(article)
            io.to_meta(article)
            i += 1


if __name__ == "__main__":
    main()
