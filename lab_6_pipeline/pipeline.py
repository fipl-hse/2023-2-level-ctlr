"""
Pipeline for CONLL-U formatting.
"""
# pylint: disable=too-few-public-methods, unused-import, undefined-variable
import pathlib
from typing import List


class CorpusManager:
    """
    Work with articles and store them.
    """

    def __init__(self, path_to_raw_txt_data: pathlib.Path) -> None:
        """
        Initialize an instance of the CorpusManager class.

        Args:
            path_to_raw_txt_data (pathlib.Path): Path to raw txt data
        """

    def _validate_dataset(self) -> None:
        """
        Validate folder with assets.
        """

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry.
        """

    def get_articles(self) -> dict:
        """
        Get storage params.

        Returns:
            dict: Storage params
        """


class ConlluToken:
    """
    Representation of the CONLL-U Token.
    """

    def __init__(self, token: spacy.tokens.Token) -> None:
        """
        Initialize an instance of the ConlluToken class.

        Args:
            token (spacy.tokens.Token): Token
        """

    def get_pos(self) -> str:
        """
        Get POS from ConlluToken.

        Returns:
            str: POS from ConlluToken
        """

    def get_conllu_text(self) -> str:
        """
        Get string representation of the token for conllu files.

        Returns:
            str: String representation of the token
        """

    def get_cleaned(self) -> str:
        """
        Get lowercase original form of a token.

        Returns:
            str: Lowercase original form of a token
        """


class ConlluSentence(SentenceProtocol):
    """
    Representation of a sentence in the CONLL-U format.
    """

    def __init__(self, position: int, text: str, tokens: list[ConlluToken]) -> None:
        """
        Initialize an instance of the ConlluSentence class.

        Args:
            position (int): Sentence position
            text (str): Sentence
            tokens (list[ConlluToken]): Tokens as ConlluToken instances
        """

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Create string representation of the sentence.

        Args:
            include_morphological_tags (bool): Flag to include morphological information

        Returns:
            str: String representation of the sentence
        """

    def get_cleaned_sentence(self) -> str:
        """
        Get lowercase representation of the sentence.

        Returns:
            str: Lowercase representation of the sentence
        """

    def get_tokens(self) -> list[ConlluToken]:
        """
        Get tokens from ConlluSentence.

        Returns:
            list[ConlluToken]: Tokens from ConlluSentence
        """


# pylint: disable=too-few-public-methods


class MorphologicalAnalysisPipeline:
    """
    Preprocess and morphologically annotate sentences into the CONLL-U format.
    """

    def __init__(self, corpus_manager: CorpusManager) -> None:
        """
        Initialize an instance of the MorphologicalAnalysisPipeline class.

        Args:
            corpus_manager (CorpusManager): CorpusManager instance
        """

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Represent text as the list of ConlluSentence.

        Args:
            text (str): Text

        Returns:
            List[ConlluSentence]: Text as the list of ConlluSentence
        """

    def run(self) -> None:
        """
        Perform basic preprocessing and write processed text to files.
        """


def main() -> None:
    """
    Entrypoint for pipeline module.
    """


if __name__ == "__main__":
    main()
