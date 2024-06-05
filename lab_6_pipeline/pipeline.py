"""
Pipeline for CONLL-U formatting.
"""
# pylint: disable=too-few-public-methods, unused-import, undefined-variable, too-many-nested-blocks
import pathlib

try:
    from networkx import DiGraph
except ImportError:  # pragma: no cover
    DiGraph = None  # type: ignore
    print('No libraries installed. Failed to import.')

import spacy_udpipe
import stanza
from core_utils.article.article import (Article, ArtifactType, get_article_id_from_filepath)
from core_utils.article.io import from_meta, from_raw, to_cleaned, to_meta
from core_utils.constants import (ASSETS_PATH, UDPIPE_MODEL_PATH)
from core_utils.pipeline import (AbstractCoNLLUAnalyzer, CoNLLUDocument, LibraryWrapper,
                                 PipelineProtocol, StanzaDocument, TreeNode)
from core_utils.visualizer import visualize
from stanza.models.common.doc import Document
from stanza.pipeline.core import Pipeline
from stanza.utils.conll import CoNLL


class InconsistentDatasetError(Exception):
    """
    IDs contain slips, numbers of meta and raw files are not equal, files are empty.
    """


class EmptyDirectoryError(Exception):
    """
    Directory is empty.
    """


class EmptyFileError(Exception):
    """
    Article file is empty
    """


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
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self._validate_dataset()
        self._storage = {}
        self._scan_dataset()

    def _validate_dataset(self) -> None:
        """
        Validate folder with assets.
        """
        path = self.path_to_raw_txt_data

        if not path.exists():
            raise FileNotFoundError

        if not path.is_dir():
            raise NotADirectoryError

        meta_files = list(path.glob('*_meta.json'))
        raw_files = list(path.glob('*_raw.txt'))

        if not meta_files or not raw_files:
            raise EmptyDirectoryError

        if len(meta_files) != len(raw_files):
            raise InconsistentDatasetError

        raw_files = sorted(raw_files, key=get_article_id_from_filepath)
        meta_files = sorted(meta_files, key=get_article_id_from_filepath)

        for ind, (raw, meta) in enumerate(zip(raw_files, meta_files)):
            if ind + 1 != get_article_id_from_filepath(raw) \
                or ind + 1 != get_article_id_from_filepath(meta) \
                or not raw.stat().st_size \
                or not meta.stat().st_size:
                raise InconsistentDatasetError()

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry.
        """
        for file in list(self.path_to_raw_txt_data.glob('*_raw.txt')):
            article_id = get_article_id_from_filepath(file)
            self._storage[article_id] = from_raw(file, Article(url=None, article_id=article_id))

    def get_articles(self) -> dict:
        """
        Get storage params.

        Returns:
            dict: Storage params
        """
        return self._storage


class TextProcessingPipeline(PipelineProtocol):
    """
    Preprocess and morphologically annotate sentences into the CONLL-U format.
    """

    def __init__(
        self, corpus_manager: CorpusManager, analyzer: LibraryWrapper | None = None
    ) -> None:
        """
        Initialize an instance of the TextProcessingPipeline class.

        Args:
            corpus_manager (CorpusManager): CorpusManager instance
            analyzer (LibraryWrapper | None): Analyzer instance
        """
        self._corpus = corpus_manager
        self.analyzer = analyzer

    def run(self) -> None:
        """
        Perform basic preprocessing and write processed text to files.
        """
        articles = self._corpus.get_articles().values()
        docs = [article.text for article in articles]
        analyzed_docs = self.analyzer.analyze(docs)
        for article, analyzed_doc in zip(articles, analyzed_docs):
            to_cleaned(article)
            article.set_conllu_info(analyzed_doc)
            self.analyzer.to_conllu(article)


class UDPipeAnalyzer(LibraryWrapper):
    """
    Wrapper for udpipe library.
    """

    _analyzer: AbstractCoNLLUAnalyzer

    def __init__(self) -> None:
        """
        Initialize an instance of the UDPipeAnalyzer class.
        """
        self._analyzer = self._bootstrap()

    def _bootstrap(self) -> AbstractCoNLLUAnalyzer:
        """
        Load and set up the UDPipe model.

        Returns:
            AbstractCoNLLUAnalyzer: Analyzer instance
        """
        model = spacy_udpipe.load_from_path(lang='ru', path=str(UDPIPE_MODEL_PATH))
        model.add_pipe(
            "conll_formatter",
            last=True,
            config={"conversion_maps": {"XPOS": {"": "_"}}, "include_headers": True},
        )
        return model

    def analyze(self, texts: list[str]) -> list[StanzaDocument | str]:
        """
        Process texts into CoNLL-U formatted markup.

        Args:
            texts (list[str]): Collection of texts

        Returns:
            list[StanzaDocument | str]: List of documents
        """
        return [self._analyzer(text)._.conll_str for text in texts]

    def to_conllu(self, article: Article) -> None:
        """
        Save content to ConLLU format.

        Args:
            article (Article): Article containing information to save
        """
        with open(article.get_file_path(kind=ArtifactType.UDPIPE_CONLLU),
                  'w', encoding='utf-8') as annotation_file:
            annotation_file.writelines(article.get_conllu_info())
            annotation_file.write('\n')


class StanzaAnalyzer(LibraryWrapper):
    """
    Wrapper for stanza library.
    """

    _analyzer: AbstractCoNLLUAnalyzer

    def __init__(self) -> None:
        """
        Initialize an instance of the StanzaAnalyzer class.
        """
        self._analyzer = self._bootstrap()

    def _bootstrap(self) -> AbstractCoNLLUAnalyzer:
        """
        Load and set up the Stanza model.

        Returns:
            AbstractCoNLLUAnalyzer: Analyzer instance
        """
        language = "ru"
        processors = "tokenize,pos,lemma,depparse"
        stanza.download(lang=language, processors=processors, logging_level="INFO")
        model = Pipeline(
            lang=language,
            processors=processors,
            logging_level="INFO",
            download_method=None
        )
        return model

    def analyze(self, texts: list[str]) -> list[StanzaDocument]:
        """
        Process texts into CoNLL-U formatted markup.

        Args:
            texts (list[str]): Collection of texts

        Returns:
            list[StanzaDocument]: List of documents
        """
        return [self._analyzer.process(Document([], text=text)) for text in texts]

    def to_conllu(self, article: Article) -> None:
        """
        Save content to ConLLU format.

        Args:
            article (Article): Article containing information to save
        """
        CoNLL.write_doc2conll(
            doc=article.get_conllu_info(),
            filename=article.get_file_path(kind=ArtifactType.STANZA_CONLLU),
        )

    def from_conllu(self, article: Article) -> CoNLLUDocument:
        """
        Load ConLLU content from article stored on disk.

        Args:
            article (Article): Article to load

        Returns:
            CoNLLUDocument: Document ready for parsing
        """
        return CoNLL.conll2doc(input_file=article.get_file_path(kind=ArtifactType.STANZA_CONLLU))


class POSFrequencyPipeline:
    """
    Count frequencies of each POS in articles, update meta info and produce graphic report.
    """

    def __init__(self, corpus_manager: CorpusManager, analyzer: LibraryWrapper) -> None:
        """
        Initialize an instance of the POSFrequencyPipeline class.

        Args:
            corpus_manager (CorpusManager): CorpusManager instance
            analyzer (LibraryWrapper): Analyzer instance
        """
        self._corpus = corpus_manager
        self._analyzer = analyzer

    def run(self) -> None:
        """
        Visualize the frequencies of each part of speech.
        """
        for article_id, article in self._corpus.get_articles().items():
            if not article.get_file_path(kind=ArtifactType.STANZA_CONLLU).stat().st_size:
                raise EmptyFileError

            from_meta(article.get_meta_file_path(), article)
            article.set_pos_info(self._count_frequencies(article))
            to_meta(article)
            visualize(article=article,
                      path_to_save=self._corpus.path_to_raw_txt_data /
                      f'{article_id}_image.png')

    def _count_frequencies(self, article: Article) -> dict[str, int]:
        """
        Count POS frequency in Article.

        Args:
            article (Article): Article instance

        Returns:
            dict[str, int]: POS frequencies
        """
        pos_freqs = {}
        for sentence in self._analyzer.from_conllu(article).sentences:
            for word in sentence.words:
                upos = word.to_dict().get('upos')
                pos_freqs[upos] = pos_freqs.get(upos, 0) + 1
        return pos_freqs


class PatternSearchPipeline(PipelineProtocol):
    """
    Search for the required syntactic pattern.
    """

    def __init__(
        self, corpus_manager: CorpusManager, analyzer: LibraryWrapper, pos: tuple[str, ...]
    ) -> None:
        """
        Initialize an instance of the PatternSearchPipeline class.

        Args:
            corpus_manager (CorpusManager): CorpusManager instance
            analyzer (LibraryWrapper): Analyzer instance
            pos (tuple[str, ...]): Root, Dependency, Child part of speech
        """

    def _make_graphs(self, doc: CoNLLUDocument) -> list[DiGraph]:
        """
        Make graphs for a document.

        Args:
            doc (CoNLLUDocument): Document for patterns searching

        Returns:
            list[DiGraph]: Graphs for the sentences in the document
        """

    def _add_children(
        self, graph: DiGraph, subgraph_to_graph: dict, node_id: int, tree_node: TreeNode
    ) -> None:
        """
        Add children to TreeNode.

        Args:
            graph (DiGraph): Sentence graph to search for a pattern
            subgraph_to_graph (dict): Matched subgraph
            node_id (int): ID of root node of the match
            tree_node (TreeNode): Root node of the match
        """

    def _find_pattern(self, doc_graphs: list) -> dict[int, list[TreeNode]]:
        """
        Search for the required pattern.

        Args:
            doc_graphs (list): A list of graphs for the document

        Returns:
            dict[int, list[TreeNode]]: A dictionary with pattern matches
        """

    def run(self) -> None:
        """
        Search for a pattern in documents and writes found information to JSON file.
        """


def main() -> None:
    """
    Entrypoint for pipeline module.
    """
    corpus_manager = CorpusManager(path_to_raw_txt_data=ASSETS_PATH)
    udpipe_analyzer = UDPipeAnalyzer()
    stanza_analyzer = StanzaAnalyzer()

    pipeline = TextProcessingPipeline(corpus_manager, udpipe_analyzer)
    pipeline.run()

    visualizer = POSFrequencyPipeline(corpus_manager, stanza_analyzer)


if __name__ == "__main__":
    main()
