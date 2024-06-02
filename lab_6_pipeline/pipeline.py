"""
Pipeline for CONLL-U formatting.
"""
# pylint: disable=too-few-public-methods, unused-import, undefined-variable, too-many-nested-blocks
import pathlib
from dataclasses import asdict

import spacy_udpipe
import stanza
from networkx import to_dict_of_lists
from networkx.algorithms.isomorphism.vf2userfunc import GraphMatcher
from networkx.classes.digraph import DiGraph
from stanza.models.common.doc import Document
from stanza.pipeline.core import Pipeline
from stanza.utils.conll import CoNLL

from core_utils.article.article import Article, ArtifactType, get_article_id_from_filepath
from core_utils.article.io import from_meta, from_raw, to_cleaned, to_meta
from core_utils.constants import ASSETS_PATH, UDPIPE_MODEL_PATH
from core_utils.pipeline import (AbstractCoNLLUAnalyzer, CoNLLUDocument, LibraryWrapper,
                                 PipelineProtocol, StanzaDocument, TreeNode)
from core_utils.visualizer import visualize


class InconsistentDatasetError(Exception):
    """
    IDs contain slips, number of meta and raw files is not equal, files are empty.
    """


class EmptyDirectoryError(Exception):
    """
    Directory is empty.
    """


class EmptyFileError(Exception):
    """
    File is empty.
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
        raw_files = list(self.path_to_raw_txt_data.glob("*_raw.txt"))
        meta_files = list(self.path_to_raw_txt_data.glob("*_meta.json"))
        if len(raw_files) != len(meta_files):
            raise InconsistentDatasetError
        sorted_raw = sorted(raw_files, key=lambda x: int(get_article_id_from_filepath(x)))
        sorted_meta = sorted(meta_files, key=lambda x: int(get_article_id_from_filepath(x)))
        for id_num, (meta, raw) in enumerate(zip(sorted_meta, sorted_raw)):
            if id_num + 1 != get_article_id_from_filepath(meta) or \
                    id_num + 1 != get_article_id_from_filepath(raw) or \
                    raw.stat().st_size == 0 or meta.stat().st_size == 0:
                raise InconsistentDatasetError

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry.
        """
        self._storage = {
            get_article_id_from_filepath(file):
                from_raw(file, Article(url=None, article_id=get_article_id_from_filepath(file)))
            for file in list(self.path_to_raw_txt_data.glob("*_raw.txt"))
        }

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
        docs = self.analyzer.analyze([article.text for article in articles])
        if docs:
            for article, doc in zip(articles, docs):
                to_cleaned(article)
                article.set_conllu_info(doc)
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
        with open(article.get_file_path(ArtifactType.UDPIPE_CONLLU), 'w',
                  encoding='utf-8') as annotation_file:
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
        stanza.download(lang="ru", processors="tokenize,pos,lemma,depparse", logging_level="INFO")
        model = Pipeline(
            lang="ru",
            processors="tokenize,pos,lemma,depparse",
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
        return self._analyzer.process([Document([], text=text) for text in texts])

    def to_conllu(self, article: Article) -> None:
        """
        Save content to ConLLU format.

        Args:
            article (Article): Article containing information to save
        """
        CoNLL.write_doc2conll(
            doc=article.get_conllu_info(),
            filename=article.get_file_path(ArtifactType.STANZA_CONLLU),
        )

    def from_conllu(self, article: Article) -> CoNLLUDocument:
        """
        Load ConLLU content from article stored on disk.

        Args:
            article (Article): Article to load

        Returns:
            CoNLLUDocument: Document ready for parsing
        """
        return CoNLL.conll2doc(input_file=article.get_file_path(ArtifactType.STANZA_CONLLU))


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
        for id_num, article in self._corpus.get_articles().items():
            if article.get_file_path(kind=ArtifactType.STANZA_CONLLU).stat().st_size == 0:
                raise EmptyFileError
            from_meta(article.get_meta_file_path(), article)
            article.set_pos_info(self._count_frequencies(article))
            to_meta(article)
            visualize(article=article,
                      path_to_save=self._corpus.path_to_raw_txt_data / f'{id_num}_image.png')

    def _count_frequencies(self, article: Article) -> dict[str, int]:
        """
        Count POS frequency in Article.

        Args:
            article (Article): Article instance

        Returns:
            dict[str, int]: POS frequencies
        """
        ud_info = self._analyzer.from_conllu(article).sentences
        pos = {}
        for conllu_sentence in ud_info:
            for word in conllu_sentence.words:
                pos_tag = word.to_dict().get('upos')
                if pos_tag:
                    pos[pos_tag] = pos.get(pos_tag, 0) + 1
        return pos


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
        self._corpus = corpus_manager
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
            graph = DiGraph()
            for word in sentence.words:
                word = word.to_dict()
                graph.add_node(word["id"],
                               label=word["upos"],
                               text=word["text"])

                graph.add_edge(word["head"],
                               word["id"],
                               label=word["deprel"])
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
        children = tuple(graph.neighbors(node_id))
        if not children or tree_node.children or node_id not in subgraph_to_graph:
            return
        for child_num in children:
            if child_num not in [node_match[0]
                                 for node_match in subgraph_to_graph.values()
                                 if node_match]:
                continue
            child_info = dict(graph.nodes(data=True))[child_num]
            child_node = TreeNode(child_info['label'],
                                  child_info['text'],
                                  [])
            tree_node.children.append(child_node)
            self._add_children(graph, subgraph_to_graph, child_num, child_node)
        return

    def _find_pattern(self, doc_graphs: list) -> dict[int, list[TreeNode]]:
        """
        Search for the required pattern.

        Args:
            doc_graphs (list): A list of graphs for the document

        Returns:
            dict[int, list[TreeNode]]: A dictionary with pattern matches
        """
        needed_pat = {}
        for (sent_id, graph) in enumerate(doc_graphs):
            ideal_graph = DiGraph()
            ideal_graph.add_nodes_from((i, {'label': label}) for i, label
                                       in enumerate(self._node_labels))
            for i in range(len(self._node_labels) - 1):
                ideal_graph.add_edge(i, i + 1)
            matcher = GraphMatcher(graph, ideal_graph,
                                   node_match=lambda n1, n2:
                                   n1.get('label', '') == n2['label'])
            pnodes = []
            for isomorph in matcher.subgraph_isomorphisms_iter():
                match_graph = graph.subgraph(isomorph)
                root_nodes = [node for node in match_graph.nodes
                              if not tuple(match_graph.predecessors(node))]
                for node_id in root_nodes:
                    tree_node = TreeNode(graph.nodes[node_id]['label'],
                                         graph.nodes[node_id]['text'],
                                         [])
                    self._add_children(graph, to_dict_of_lists(match_graph), node_id, tree_node)
                    pnodes.append(tree_node)
            if pnodes:
                needed_pat[sent_id] = pnodes
        return needed_pat

    def run(self) -> None:
        """
        Search for a pattern in documents and writes found information to JSON file.
        """
        for article in self._corpus.get_articles().values():
            conllu = self._analyzer.from_conllu(article)
            graphs = self._make_graphs(conllu)
            p_matches = self._find_pattern(graphs)
            dict_with_matches = {}
            for sent_id, matches in p_matches.items():
                temp_list = []
                for match in matches:
                    temp_list.append(asdict(match))
                dict_with_matches[sent_id] = temp_list
            article.set_patterns_info(dict_with_matches)
            to_meta(article)


def main() -> None:
    """
    Entrypoint for pipeline module.
    """
    corpus_manager = CorpusManager(path_to_raw_txt_data=ASSETS_PATH)
    udpipe_analyzer = UDPipeAnalyzer()
    pipeline = TextProcessingPipeline(corpus_manager, udpipe_analyzer)
    pipeline.run()
    stanza_analyzer = StanzaAnalyzer()
    pipeline = TextProcessingPipeline(corpus_manager, stanza_analyzer)
    pipeline.run()
    visualizer_pos = POSFrequencyPipeline(corpus_manager, stanza_analyzer)
    visualizer_pos.run()
    visualizer_pat = PatternSearchPipeline(corpus_manager,
                                           stanza_analyzer,
                                           ("VERB", "NOUN", "ADP"))
    visualizer_pat.run()


if __name__ == "__main__":
    main()
