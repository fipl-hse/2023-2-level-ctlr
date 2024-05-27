"""
Pipeline for CONLL-U formatting.
"""
# pylint: disable=too-few-public-methods, unused-import, undefined-variable, too-many-nested-blocks
import pathlib

import networkx as nx
import spacy_udpipe
import stanza
from networkx import DiGraph
from networkx.algorithms.isomorphism import GraphMatcher
from stanza.models.common.doc import Document
from stanza.pipeline.core import Pipeline
from stanza.utils.conll import CoNLL

from core_utils.article.article import Article, ArtifactType, get_article_id_from_filepath
from core_utils.article.io import from_meta, from_raw, to_cleaned, to_meta
from core_utils.constants import ASSETS_PATH, UDPIPE_MODEL_PATH
from core_utils.pipeline import (AbstractCoNLLUAnalyzer, CoNLLUDocument, LibraryWrapper,
                                 PipelineProtocol, StanzaDocument, TreeNode)
from core_utils.visualizer import visualize


class EmptyDirectoryError(Exception):
    """
    Raising an error when the directory is empty
    """


class InconsistentDatasetError(Exception):
    """
    IDs contain slips, number of meta and raw files is not equal, files are empty;
    """


class EmptyFileError(Exception):
    """
    I don't khow for what
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
        self._storage = {}
        self._validate_dataset()
        self._scan_dataset()

    def _validate_dataset(self) -> None:
        """
        Validate folder with assets.
        """
        if not self.path_to_raw_txt_data.exists():
            raise FileNotFoundError

        if not self.path_to_raw_txt_data.is_dir():
            raise NotADirectoryError

        if not any(self.path_to_raw_txt_data.iterdir()):
            raise EmptyDirectoryError

        meta_files = sorted(self.path_to_raw_txt_data.glob('*_meta.json'),
                            key=get_article_id_from_filepath)
        txt_files = sorted(self.path_to_raw_txt_data.glob('*_raw.txt'),
                           key=get_article_id_from_filepath)

        if len(txt_files) != len(meta_files):
            raise InconsistentDatasetError

        for index, (meta, raw) in enumerate(zip(meta_files, txt_files), start=1):
            if index != get_article_id_from_filepath(meta) or \
                    index != get_article_id_from_filepath(raw) or \
                    not meta.stat().st_size or not raw.stat().st_size:
                raise InconsistentDatasetError

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry.
        """
        txt_files = sorted(self.path_to_raw_txt_data.glob('*_raw.txt'))
        for raw in txt_files:
            article_id = get_article_id_from_filepath(raw)
            self._storage[article_id] = from_raw(path=raw, article=Article(None, article_id))

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
        doc_conllu = []
        if self.analyzer:
            doc_conllu = self.analyzer.analyze([article.text for article in articles])

        for index, article in enumerate(articles):
            to_cleaned(article)
            if self.analyzer and doc_conllu:
                article.set_conllu_info(doc_conllu[index])
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
        model = spacy_udpipe.load_from_path(
            lang="ru",
            path=str(UDPIPE_MODEL_PATH)
        )
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
            annotation_file.write(article.get_conllu_info())
            annotation_file.write("\n")


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
        return Pipeline(
            lang=language,
            processors=processors,
            logging_level="INFO",
            download_method=None
        )

    def analyze(self, texts: list[str]) -> list[StanzaDocument]:
        """
        Process texts into CoNLL-U formatted markup.

        Args:
            texts (list[str]): Collection of texts

        Returns:
            list[StanzaDocument]: List of documents
        """
        return self._analyzer.process([Document([], text=text) for text in texts])

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
        self.corpus_manager = corpus_manager
        self.analyzer = analyzer

    def run(self) -> None:
        """
        Visualize the frequencies of each part of speech.
        """
        articles = self.corpus_manager.get_articles()

        for index, article in articles.items():
            if (article.get_file_path(kind=ArtifactType.STANZA_CONLLU)
                    .stat().st_size == 0):
                raise EmptyFileError

            article = from_meta(article.get_meta_file_path(), article)
            pos_dict = self._count_frequencies(article)
            article.set_pos_info(pos_dict)
            to_meta(article)

            visualize(article, self.corpus_manager.path_to_raw_txt_data / f'{index}_image.png')

    def _count_frequencies(self, article: Article) -> dict[str, int]:
        """
        Count POS frequency in Article.

        Args:
            article (Article): Article instance

        Returns:
            dict[str, int]: POS frequencies
        """
        pos_dict = {}
        for pos_tag in self.analyzer.from_conllu(article).get('upos'):
            pos_dict[pos_tag] = pos_dict.get(pos_tag, 0) + 1
        return pos_dict


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
        self._corpus_manager = corpus_manager
        self._analyzer = analyzer
        self._node_labels = pos

    def _make_graphs(self, doc: CoNLLUDocument) -> list[DiGraph]:
        """
        Make graphs for a document.

        Args:
            doc (CoNLLUDocument): Document for patterns searching

        Returns:
            list[DiGraph]: Graphs for the sentences in the document
        """
        graphs = []

        for sentence in doc.sentences:
            graph = nx.DiGraph()

            for word in sentence.words:
                word = word.to_dict()
                graph.add_node(word['id'], label=word['upos'], text=word['text'])

                if word['head'] != 0:  # Root tokens have a head of 0
                    graph.add_edge(word['head'], word['id'], label=word['deprel'])

            graphs.append(graph)

        return graphs

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
        children = tuple(graph.successors(node_id))
        if not children or tree_node.children or node_id not in subgraph_to_graph.keys():
            return None
        target_vertices = {vertex[0] for vertex in subgraph_to_graph.values() if vertex}
        for child_id in children:
            if child_id not in target_vertices:
                continue

            child_node_info = graph.nodes[child_id]
            child_node = TreeNode(
                child_node_info.get('label'),
                child_node_info.get('text'),
                []
            )
            tree_node.children.append(child_node)
            self._add_children(graph, subgraph_to_graph, child_id, child_node)
        return None

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
    corpus_manager = CorpusManager(ASSETS_PATH)
    analyzer = UDPipeAnalyzer()
    pipeline = TextProcessingPipeline(corpus_manager, analyzer)
    pipeline.run()

    stanza_analyzer = StanzaAnalyzer()
    pipeline = TextProcessingPipeline(corpus_manager, stanza_analyzer)
    pipeline.run()

    visualizer = POSFrequencyPipeline(corpus_manager, stanza_analyzer)
    visualizer.run()

    pattern_searcher = PatternSearchPipeline(corpus_manager, stanza_analyzer,
                                             ("VERB", "NOUN", "ADP"))
    pattern_searcher.run()


if __name__ == "__main__":
    main()
