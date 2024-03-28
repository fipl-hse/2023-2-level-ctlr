.. _pipeline-label:

Laboratory work №6. Process raw data
====================================

.. toctree::
    :maxdepth: 1
    :titlesonly:
    :caption: Full API

    lab_6_pipeline.api.rst

Python competencies required to complete this tutorial:

   -  working with external dependencies, going beyond Python standard
      library;
   -  working with external modules: local and downloaded from PyPi;
   -  working with files: create/read/update;
   -  applying basic cleaning techniques to the raw text: tokenization,
      lemmatization etc.;
   -  extracting linguistic features from the raw text: part of speech,
      case etc.

Processing data breaks down in the following steps:

1. Loading raw data.
2. Tokenizing the text.
3. Performing necessary transformations, such as lemmatization or
   stemming.
4. Extracting valuable information from the text, such as detect each
   word part of speech.
5. Saving necessary information.

As a part of the second milestone, you need to implement processing
logic as a ``pipeline.py`` module. When it is run as a standalone Python
program, it should perform all aforementioned stages.

During this assignment you will be working with the UD text description
format (``.conllu`` extension). Refer to :ref:`ud-format-label`
for the explanation on linguistic information extraction,
mappings to ``pymystem3`` and ``pymorphy2``, as well as fields description.

Executing pipeline
------------------

Example execution (``Windows``):

.. code:: bash

   python pipeline.py

Expected result:

1. ``N`` raw texts previously collected by scrapper are processed.
2. Each article has a processed version (or versions) saved
   in the ``tmp/articles`` directory.

An example ``tmp`` directory content for mark 6:

.. code:: text

   +-- 2023-2-level-ctlr
       +-- tmp
           +-- articles
               +-- 1_raw.txt <- the paper with the ID (from scrapper.py run)
               +-- 1_meta.json <- the paper meta-information (from scrapper.py run)
               +-- 1_cleaned.txt <- processed text with no punctuation (by pipeline.py run)
               +-- 1_pos_conllu.conllu <- processed text in the UD format (by pipeline.py run)

.. hint:: When using CI (Continuous Integration), generated
          ``processed-dataset.zip`` is available in build artifacts. Go to
          ``Actions`` tab in GitHub UI of your fork, open the last job and if
          there is an artifact, you can download it.

Configuring pipeline
--------------------

Processing behavior must follow several steps:

1. Pipeline takes a raw dataset that is collected by ``scrapper.py`` and
   placed at ``ASSETS_PATH`` (see ``constants.py`` for a particular
   place).
2. Pipeline goes through each raw file, for example ``1_raw.txt``.
3. Pipeline processes each text, sentence, word token and extracts
   linguistic information.
4. Pipeline saves extracted information into the file with the same id
   for each article processed, for example ``1_pos_conllu.conllu``.

Assessment criteria
-------------------

You state your ambition on the mark by editing the file
``target_score.txt``. For example:

.. code:: bash

   6

would mean that you have made tasks for mark ``6`` and request mentors
to check if you can get it.

1. Desired mark **4**:

   1. ``pylint`` level: ``5/10``.
   2. Pipeline validates that raw dataset has a proper structure and
      fails appropriately if the latter is incorrect. Criteria:

      1. Dataset exists (there is a folder).
      2. Dataset is not empty (there are files inside).
      3. Dataset is balanced - there are only files that follow the
         naming conventions:

         1. ``N_raw.txt`` where N is a valid number.
         2. Numbers of articles are from 1 to N without any slips.

   3. Pipeline tokenizes text in each file, removes punctuation, and
      casts it to the lower case (no *lemmatization* or *tagging*).
   4. Pipeline produces ``N_cleaned.txt`` files in the ``tmp/articles``.

      1. `Example raw text
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
         lab_6_pipeline/tests/test_files/1_raw.txt>`__ and `Desired output
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/lab_6_pipeline/
         tests/test_files/reference_score_four_test.txt>`__.

2. Desired mark **6**:

   1. ``pylint`` level: ``7/10``.
   2. All requirements for the mark **4**.
   3. Pipeline uses ``pymystem3`` library to perform lemmatization and
      POS tagging.
   4. Pipeline should define ID, FORM, LEMMA, and POS information in the
      resulting ``.conllu`` file.
   5. Pipeline produces ``N_pos_conllu.conllu`` files with text tagging
      for each article.

      1. `Example raw text
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
         lab_6_pipeline/tests/test_files/1_raw.txt>`__ and `Desired output
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/lab_6_pipeline/
         tests/test_files/reference_score_six_test.conllu>`__.

3. Desired mark **8**:

   1. ``pylint`` level: ``10/10``.
   2. All requirements for the mark **6**.
   3. Pipeline uses ``pymystem3`` library to perform morphological tags
      extraction (``pymystem3`` tags are represented in angle brackets).
   4. Pipeline should define FEATS alongside ID, FORM, LEMMA, and POS
      fields information in the resulting ``.conllu`` file.
   5. Pipeline produces ``N_morphological_conllu.conllu`` files with
      extended morphological information for each article, e.g. word
      animacy.

      1. `Example raw text
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
         lab_6_pipeline/tests/test_files/1_raw.txt>`__ and `Desired output
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/lab_6_pipeline/
         tests/test_files/reference_score_eight_test.conllu>`__.

4. Desired mark **10**:

   1. ``pylint`` level: ``10/10``.
   2. All requirements for the mark **8**.
   3. An additional pipeline is introduced that:

      1. Uses backup ``pymorphy2`` analyzer and backup tag converter for
         ``NOUN`` tags processing.
      2. Produces ``N_full_conllu.conllu`` files with extended
         morphological information for ``NOUN`` by ``pymorphy2``.

         1. `Example raw text
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
         lab_6_pipeline/tests/test_files/1_raw.txt>`__ and `Desired output
         <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/lab_6_pipeline/
         tests/test_files/reference_score_ten_test.conllu>`__

   4. An additional pipeline is introduced ``pos_frequency_pipeline.py``
      that:

      1. Collects frequencies of POS in each text.
      2. Extends ``N_meta.json`` files with this information.
      3. Visualizes this distribution as ``.png`` files that are created
         for each article and saved into ``N_image.png`` files.

         1. `Example meta info
            <https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
            lab_6_pipeline/tests/test_files/1_meta.json>`__ and `Desired output
            <https://github.com/fipl-hse/2022-2-level-ctlr/blob/main/
            core_utils/tests/test_files/reference_image.png>`__

Implementation tactics
----------------------

All logic for instantiating and using needed abstractions should be
implemented in a special block of the module ``pipeline.py``:

.. code:: python

   def main():
       print('Your code goes here')

   if __name__ == '__main__':
       main()

Stage 0. Prerequisites
~~~~~~~~~~~~~~~~~~~~~~

-  ``scrapper.py`` implementation

You will not be able to start your implementation if there is no
``scrapper.py`` implementation.
Make sure you implemented and passed ``scrapper.py`` assignment first.

-  Ensure you only use ``pathlib`` to work with file paths

As we discussed during lectures it is always better to have something
designed specifically for the given task. Comparing ``os`` and
``pathlib`` modules, the latter is the one that is designed for most
file system related operations. Make sure you use only ``pathlib`` in
the code you write.

.. important:: Do not change modules external to your code, for example
               ``core_utils/article/article.py`` - consider them as not available
               for installation. If you see a way to improve external modules,
               propose them in a separate PR - mentors will review them separately
               and give you bonuses as any improvements are appreciated.

Stage 1. Introduce a corpus abstraction: ``CorpusManager``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As we discussed multiple times, when we are working from our Python
programs with the real world entities, we need to emulate their behavior
by new abstractions. If we think of the Pipeline and consider the Single
Responsibility Principle, we will quickly realize that it is not the
responsibility of the Pipeline to know where the dataset files are
located and how to read/write to them, etc. Therefore, we need a new
abstraction to be responsible for such tasks. We call it
:py:class:`lab_6_pipeline.pipeline.CorpusManager`.

Stage 1.1. Introduce ``CorpusManager`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`lab_6_pipeline.pipeline.CorpusManager` is an entity
that knows where the dataset is placed
and what are the available files of this dataset.

It should be instantiated with the following instruction:

.. code:: python

   corpus_manager = CorpusManager(path_to_raw_txt_data=ASSETS_PATH)

The :py:class:`lab_6_pipeline.pipeline.CorpusManager` instance validates
the dataset provided and saves all the constructor arguments in attributes
with corresponding names. Each instance should also have an additional
attribute ``self._storage`` of a dictionary type and filled with
information about the files. Read about
the filling instructions in the **Stage 1.3**.

.. note:: Remember to use ``pathlib`` to create file path object.

Stage 1.2. Implement a method for a dataset validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pipeline expects that dataset is collected by scrapper. It must not
start working if dataset is invalid. The very first thing that should
happen after :py:class:`lab_6_pipeline.pipeline.CorpusManager`
is instantiated is a dataset validation.
Implement :py:meth:`lab_6_pipeline.pipeline.CorpusManager._validate_dataset`
method.

.. note:: Remember to use ``pathlib`` module in order
          to operate paths.

.. note:: Call this method during initialization.

When dataset is valid, method returns ``None``. Otherwise:

1. One of the following errors is thrown:

   -  ``FileNotFoundError``: file does not exist;
   -  ``NotADirectoryError``: path does not lead to directory;
   -  ``InconsistentDatasetError``: IDs contain slips, number of meta
      and raw files is not equal, files are empty;

      -  For **mark 4**, check that dataset contains no slips in IDs of
         raw files and files are not empty.

   -  ``EmptyDirectoryError``: directory is empty.

2. Script immediately finishes execution.

.. note:: While validating dataset, ignore files which are named not
          using formats.

Stage 1.3. Implement a method for filling files storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

During initialization of :py:class:`lab_6_pipeline.pipeline.CorpusManager`,
it should scan the provided folder path and register each dataset entry.
All the storage is represented as ``self._storage`` attribute.
Filling the storage should be done by executing
:py:meth:`lab_6_pipeline.pipeline.CorpusManager._scan_dataset` method.

.. note:: Call this method during initialization and save the results in
          ``self._storage`` attribute.

.. note:: Can you explain why the name of the method starts with an
          underscore?

The method should contain logic for iterating over the content of the
folder, finding all ``N_raw.txt`` files and creating
:py:class:`core_utils.article.article.Article` instance for each file.

.. note:: The :py:class:`core_utils.article.article.Article` constructor
          expects URL as the first argument. It
          should be safe to pass ``None`` instead of the real URL. Pipeline
          does not need to know where was the article downloaded from.
          See :ref:`ctlr-article-label`.

As it was stated before, ``self._storage`` attribute is just a
dictionary. Keys are ids of the files, values are instances of the
:py:class:`core_utils.article.article.Article` class.
For example, pipeline finds a file ``1_raw.txt``.
Then we put new pair to the storage:

.. code:: python

   self._storage[1] = Article(url=None, article_id=1)

Stage 1.4. Implement a method for retrieval of files storage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``self._storage`` attribute is not a part of
:py:class:`lab_6_pipeline.pipeline.CorpusManager`
interface, therefore we need a special getter - a method that just
returns a storage value. At this stage, you need to implement
:py:meth:`lab_6_pipeline.pipeline.CorpusManager.get_articles` method.

.. note:: Can you explain why we might need getters?

Eventually, :py:class:`lab_6_pipeline.pipeline.CorpusManager` should return
a dictionary of :py:class:`core_utils.article.article.Article` instances via
:py:meth:`lab_6_pipeline.pipeline.CorpusManager.get_articles` method.

.. note:: The :py:class:`lab_6_pipeline.pipeline.CorpusManager` knows where are the files,
          it can easily find them by id, but it is not its responsibility
          to perform actual file reads and writes.
          See ``core_utils/article/io.py`` module for article
          save/read functionality.

Stage 2. Introduce abstraction for processing texts: ``MorphologicalAnalysisPipeline``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get a mark not lower than 4, your pipeline must perform basic text
preprocessing:

1. Tokenize sentences (split into words).
2. Lowercase each token.
3. Remove punctuation.

After implementation of preprocessing, your pipeline must save results
in the files with the names following the pattern ``N_cleaned.txt``. See
examples for a better understanding: `Raw text
<https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/1_raw.txt>`__ - `Desired output
<https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/reference_score_four_test.txt>`__.

Stage 2.1. Implement simplified logic of ``ConlluToken`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You need to define abstractions responsible for managing data. We start
with :py:class:`lab_6_pipeline.pipeline.ConlluToken` abstraction.
It should be initialized with token string as a parameter:

.. code:: python

   conllu_token = ConlluToken(text='мама')

The :py:class:`lab_6_pipeline.pipeline.ConlluToken` abstraction
should implement returning lowercased original form of a token
and removing punctuation by
:py:meth:`lab_6_pipeline.pipeline.ConlluToken.get_cleaned` method:

.. attention:: For mark 4 you are not required to fill in and implement
               morphological parameters related methods.

Stage 2.2. Implement simplified logic of ``ConlluSentence`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`lab_6_pipeline.pipeline.ConlluSentence` abstraction
stores the representation of the sentence.
This abstraction should define
:py:meth:`lab_6_pipeline.pipeline.ConlluSentence.get_cleaned_sentence`
method for getting lowercased sentence with no punctuation.

.. note:: In this method it is mandatory to call
          :py:meth:`lab_6_pipeline.pipeline.ConlluToken.get_cleaned` method.

Stage 2.3. Implement simplified logic of ``MorphologicalAnalysisPipeline``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All of the above stages are necessary for implementing simplified
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline` abstraction.
It takes the raw text of the article and saves the processed
(lowercased with no punctuation) text to a file ``N_cleaned.txt``.
The abstraction should have ``self._corpus`` attribute which represents your
:py:class:`lab_6_pipeline.pipeline.CorpusManager` abstraction.

It should be instantiated with the following instruction:

.. code:: python

   pipeline = MorphologicalAnalysisPipeline(corpus_manager)

It is executed with a simple interface method
:py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
that you need to implement. Once executed,
:py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
iterates through the available articles taken from
:py:class:`lab_6_pipeline.pipeline.CorpusManager`,
reads each file, performs basic
preprocessing and writes processed text to files.

.. note:: It is mandatory to get articles with the
          :py:meth:`lab_6_pipeline.pipeline.CorpusManager.get_articles` method
          and to read article with the
          :py:func:`core_utils.article.io.from_raw` function.

.. tip:: Try to implement
         :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
         in a way that it goes through the articles collected by
         :py:meth:`lab_6_pipeline.pipeline.CorpusManager.get_articles`,
         reads each of them using the :py:func:`core_utils.article.io.from_raw`
         function, stores the sentences in the article using
         :py:meth:`core_utils.article.article.Article.set_conllu_sentences`,
         and then writes to the file as a processed article using the
         :py:func:`core_utils.article.io.to_cleaned` function. At least you
         will see that everything works to this moment and you can proceed to
         implementing core logic of pipeline.

All preprocessing logic is encapsulated in the protected
:py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline._process` method.
It takes the text of the article, splits it into sentences and returns a
list of :py:class:`lab_6_pipeline.pipeline.ConlluSentence`.

.. note:: The :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline._process`
          method should be called in the
          :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run` method.

Stage 2.4. Save the results of text preprocessing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important:: **Stages 0-2.4** are required to get the **mark 4**.

In order to save each article to its separate file, inspect the
``core_utils/article/io.py`` module.
Use :py:func:`core_utils.article.io.to_cleaned` function
to save cleaned text to the appropriate folder. Call this
function with the article instance you want to save text for.

The function generates a file with a name ``N_cleaned.txt``, where ``N``
is the index of your article in the ``tmp/articles`` directory.

.. note:: It is mandatory to save generated text to file in the
          :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run` method.

Stage 3. Perform morphological analysis via ``MorphologicalAnalysisPipeline``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get a mark not lower than 6, your pipeline, in addition to mark 4
requirements, must perform morphological text analysis for each article
using ``pymystem3`` library and save the result in the file with the
name following the pattern ``N_pos_conllu.conllu``.
See examples for a better understanding: `Raw text
<https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/1_raw.txt>`__ - `Desired output
<https://github.com/fipl-hse/2023-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/reference_score_six_test.conllu>`__.

File with ``.conllu`` extension means that it corresponds to the UD
format. Starting with the mark 6 you are required to save results of
morphological text analysis in the UD format. For better understanding
of the format fields see :ref:`ud-format-label`.

.. note:: Specifically for mark 6 your pipeline should define ID, FORM,
          LEMMA, and POS information in the resulting ``.conllu`` file.

As all article text information storing and managing is done by the
:py:class:`core_utils.article.article.Article` abstraction,
see :ref:`ctlr-article-label` before proceeding to the next stages.

Stage 3.1. Define ``MorphologicalTokenDTO`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``lab_6_pipeline.pipeline.MorphologicalTokenDTO``
abstraction stores the following information for each token:

-  lemma
-  part of speech
-  morphological tags

All class fields should be optional for initialisation. It means if
there is no morphological tags information the field should be left as
an empty string.

.. note:: For mark 6 you need only lemma and POS information, so
          ``tags`` field should be empty.

Stage 3.2. Extend ``ConlluToken`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After implementing the ``lab_6_pipeline.pipeline.MorphologicalTokenDTO``
which is responsible for storing morphological information,
you need to add this information to the
:py:class:`lab_6_pipeline.pipeline.ConlluToken` abstraction.

After that define getting and setting methods for morphological
information:

- ``lab_6_pipeline.pipeline.ConlluToken.set_morphological_parameters``
- ``lab_6_pipeline.pipeline.ConlluToken.get_morphological_parameters``

Stage 3.3. Adapt ``ConlluToken`` string representation for ``.conllu`` files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You also have to define
:py:meth:`lab_6_pipeline.pipeline.ConlluToken.get_conllu_text` method
for token’s string representation for ``.conllu`` files.

In this method you have to create a string with the following features
which must be joined with a tabulation ``\t``:

-  ``position``
-  ``text``
-  ``lemma`` which will be filled with lemma. You are going to do that
   in **Stage 3.5**.
-  ``pos``
-  ``xpos`` which is filled with ``_``
-  ``feats`` which is filled with ``_`` so far. You will need it for
   mark 8.
-  ``head`` which is filled with ``0``
-  ``deprel`` which is filled with ``root``
-  ``deps`` which is filled with ``_``
-  ``misc`` which is filled with ``_``

.. note:: The last four fields will be filled certain way as the UD
          format demands it, but these fields will not be needed in our
          laboratory work.

Stage 3.4. Extend ``ConlluSentence`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Also in :py:class:`lab_6_pipeline.pipeline.ConlluSentence` abstraction
you have to create the sentence’s string representation for ``.conllu`` files.
For this aim you need to define the following methods:

- ``lab_6_pipeline.pipeline.ConlluSentence._format_tokens``
  which formats tokens per newline;
- :py:meth:`lab_6_pipeline.pipeline.ConlluSentence.get_conllu_text`
  which creates the sentence’s string representation that includes:

    -  ``sent_id``
    -  ``text``
    -  ``tokens``

``sent_id`` and ``text`` should look like the following way:

.. code:: python

   f'# sent_id = {self._position}\n'
   f'# text = {self._text}\n'

.. note:: To write ``tokens`` you have to call
          ``lab_6_pipeline.pipeline.ConlluSentence._format_tokens`` method.

.. note:: Parameter ``include_morphological_tags`` is responsible for
          displaying morphological tags. For implementation on mark 6 you don’t
          need to display them.

Stage 3.5. Extend ``MorphologicalAnalysisPipeline`` with morphological analysis logic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After implementing abstractions for storing and managing morphological
data you need to define overall processing logic to fill abstractions
defined with data and save processing result in the UD format. All
processing and filling actions is the responsibility of pipeline.
So you need to extend
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline` pipeline.

For mark 6, apart from tokenization, punctuation removal and casting to
lowercase, you must implement the following processing:

1. Setting token id (that is ``ID`` field in the UD-formatted file).
2. Setting token text (that is ``FORM`` field in the UD-formatted file).
3. Lemmatization (that is ``LEMMA`` field in the UD-formatted file).
4. POS tagging (that is ``POS`` field in the UD-formatted file).

.. note:: For more information about these fields see :ref:`ud-format-label`.

Stage 3.6. Extracting base morphological information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline`
is executed with the same interface method
:py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
as described during previous stages. The only
difference is inside processing logic. Once executed:

-  pipeline goes over each :py:class:`core_utils.article.article.Article`
   instance and gets raw text:

   -  for each sentence in raw text pipeline fills
      :py:class:`lab_6_pipeline.pipeline.ConlluSentence`;
   -  for each token in the sentence pipeline fills
      :py:class:`lab_6_pipeline.pipeline.ConlluToken`;
   -  for each :py:class:`lab_6_pipeline.pipeline.ConlluToken` instance pipeline fills
      ``lab_6_pipeline.pipeline.MorphologicalTokenDTO``;
   -  to get morphological information for
      ``lab_6_pipeline.pipeline.MorphologicalTokenDTO``
      pipeline uses ``pymystem3`` library.

-  pipeline sets :py:class:`core_utils.article.article.Article`
   conllu sentences field using
   :py:meth:`core_utils.article.article.Article.set_conllu_sentences` method;
-  pipeline saves processing result using
   :py:func:`core_utils.article.io.to_conllu` function.

To extract lemma and POS information you need to use ``pymystem3``
library.

.. note:: It is recommended to rely on ``pymystem3`` ability to process
          text as a whole and perform tokenization, lemmatization and
          morphological analysis at once. There are several reasons to do that,
          but from the linguistic perspective it would be interesting for you
          to remember that context-aware lemmatization works better than
          lemmatization of each word separately.

Use the following way to analyze the text:

.. code:: python

   result = Mystem().analyze(text)

Here, ``text`` is the text that you want to process, e.g. raw text of
the article, and ``result`` is the result of morphological analysis.
Inspect the ``result`` as you need. It stores all information required
for the assignment.

.. note:: Use ``debug`` or ``print`` to inspect the content of ``result``
          - you will find everything you need there.

.. hint:: ``result['text']`` is likely to have the original word. Use the
          same approach to find POS information and normalized form.

Keep in mind that all processing logic is encapsulated in the protected
:py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline._process`
pipeline method as described previously.

.. note:: The only punctuation mark used in resulting ``.conllu`` files
          is a dot at the end of the sentence. Make sure you remove or ignore
          other punctuation marks.

.. note:: Since conversion to UD requires us to provide POS tag to every
          entity and ``pymystem3`` and ``pymorphy2`` do not give any tag to
          numbers and punctuation, you need to identify such tokens as numbers
          and punctuation and map them to appropriate UD tags: ``PUNCT`` and ``NUM``.

Stage 3.7. Implement ``MystemTagConverter`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you get word POS info, it is not presented in an appropriate
format. You need to convert it into the UD format. For more information
about the UD format and tag conversion see :ref:`ud-format-label`.

The :py:class:`core_utils.article.ud.TagConverter` abstraction
is responsible for tags conversion between different formats.
You need to inherit interface given and implement the following
abstraction inside the ``pipeline.py`` file:

.. code:: py

   class MystemTagConverter(TagConverter):
       pass

The ``lab_6_pipeline.pipeline.MystemTagConverter`` instance
should be initialised with path to the tag mappings file,
e.g. information about the correspondence of one
format tags to another format tags. You need to define tag mappings in
the JSON format under the ``lab_6_pipeline/data`` directory. Again, see
:ref:`ud-format-label` and :ref:`ud-mapping-label` for more information on
the UD format and its mapping with other formats.

.. note:: JSON file with ``pymystem3`` tag mappings should be named
          ``mystem_tags_mapping.json``.

After initialising the ``lab_6_pipeline.pipeline.MystemTagConverter``
instance, it should extract mapping information from the file provided inside its
constructor. All mapping information should be filled into the class
attribute field.

Specifically for mark 6 you need to convert POS information from
``pymystem3`` format into the UD format. For example, ``pymystem3``
analysis result string ``A=им,ед,полн,жен`` should be converted into
``ADJ`` UD POS tag. To do this implement
``lab_6_pipeline.pipeline.MystemTagConverter.convert_pos`` method.
It extracts POS tag from ``pymystem3`` analysis string and converts
it into the UD format.

.. note:: Make sure you convert ``pymystem3`` POS tag right after getting
          it as a result of text analysis.
          The ``lab_6_pipeline.pipeline.MorphologicalTokenDTO`` instance
          ``pos`` field should be filled with the UD formatted POS tag.
          The ``lab_6_pipeline.pipeline.MystemTagConverter`` instance
          should be initialised as a field of
          :py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline`.

Stage 3.8. Save the results of text POS tagging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important:: **Stages 0-3.8** are required to get the **mark 6**.

In order to save each article to its separate file, inspect the
``core_utils/article/io.py`` module. Use
:py:func:`core_utils.article.io.to_conllu` function to save the result
of text POS tagging to the appropriate folder.
Call this function with the article instance you want to save text for.

.. attention:: ``include_morphological_tags`` and ``include_pymorphy_tags``
               parameters should be ``False``.

The function generates a file with a name ``N_pos_conllu.conllu``, where
``N`` is the index of your article in the ``tmp/articles`` directory.

.. note:: It is mandatory to save generated text to file in the
          :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
          method.

Stage 4. Deepen morphological analysis with ``MorphologicalAnalysisPipeline``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get a mark not lower than 8, your
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline`
should also produce files with extended morphological information for
each article, e.g. word animacy, and save the result in the file with
the name following the pattern ``N_morphological_conllu.conllu``.
See examples for a better understanding: `Raw text
<https://github.com/fipl-hse/2022-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/1_raw.txt>`__ - `Desired output
<https://github.com/fipl-hse/2022-2-level-ctlr/blob/main/
lab_6_pipeline/tests/test_files/reference_score_eight_test.conllu>`__.

.. note:: For mark 8 your pipeline should fill FEATS alongside ID, FORM,
          LEMMA, and POS fields information in the resulting ``.conllu`` file.

Stage 4.1. Extend logic of ``MorphologicalAnalysisPipeline`` with additional analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As you already know, ``pymystem3`` library allows you to get
morphological analysis for a particular word. During previous stages you
extracted only lemma and POS tag from ``pymystem3`` analysis. For
example, analyzing word ``красивая`` you have got a lemmatized version -
``красивый`` - and its POS tag - ``A`` which you subsequently have
converted into the UD format.

For mark 8 you need to implement deeper morphological analysis with
``pymystem3`` library by obtaining the morphological features of the
word. For example, when analysing word ``красивая``, ``pymystem3`` gives
the following result: ``A=им,ед,полн,жен``. You need to take
``им,ед,полн,жен`` tags, convert them into the UD-formatted string and
save alongside other morphological information in the UD format (that is
``FEATS`` field in the UD-formatted file).

.. note:: It is still
          :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline._process`
          method that contains all the processing logic,
          including additional analysis done with ``pymystem3``.

.. note:: ``pos``, ``lemma``, ``tags`` fields of
          ``lab_6_pipeline.pipeline.MorphologicalTokenDTO``
          abstraction should be initialized during
          processing with word morphological features converted into the UD
          format. The ``tags`` field is used later to fill the ``FEATS`` field
          in the UD-formatted file.

Stage 4.2. Extend mapping information and ``MystemTagConverter`` conversion logic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First of all, you need to extend JSON file with mapping information, as
now you are working with additional morphological attributes. Think
about ``pymystem3`` and UD format attributes correspondence and create
mappings accordingly.

As you now retrieve extended morphological information you need to
extend the ``lab_6_pipeline.pipeline.MystemTagConverter``
abstraction with
``lab_6_pipeline.pipeline.MystemTagConverter.convert_morphological_tags``
method. It takes ``pymystem3`` word attributes string, extracts all
morphological features and converts them in the UD format according to
mapping information. For example ``pymystem3`` word attributes string
``A=им,ед,полн,жен`` should be converted into the
``Case=Nom|Gender=Fem|Number=Sing`` string according to UD format.

.. note:: To have a better understanding of conversion logic
          see :ref:`ud-format-label`.

Stage 4.3. Save the results of text double-tagging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important:: **Stages 0-4.3** are required to get the **mark 8**.

In order to save each article to its separate
``N_morphological_conllu.conllu`` file, call
:py:func:`core_utils.article.io.to_conllu` function
with each of your articles instances as parameter.

.. attention:: The ``include_morphological_tags`` parameter should be ``True``
               and the ``include_pymorphy_tags`` parameter should be ``False``.
               Moreover, if ``include_morphological_tags`` parameter of
               :py:meth:`lab_6_pipeline.pipeline.ConlluToken.get_conllu_text`
               method is ``False``, you will not save morphological tags.

.. note:: It is mandatory to save generated text to file in the
          :py:meth:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline.run`
          method.

Stage 5. Improve morphological analysis performance and visualise statistics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For mark 10 you need to refine the logic of the existing
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline`
pipeline by making a more flexible
``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline``
version. Mark 10 implies not just extracting information from text,
but also statistical processing and visualization of the resulting information.
For this purpose you are going to introduce
:py:class:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline`.
Let us start with improving morphological pipeline processing logic.

Stage 5.1. Introduce additional ``pymorphy2`` backup analyzer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You have used ``pymystem3`` analyzer before, and you may have noticed
that the analyzer provides quite accurate analysis of tokens in some
places, but in other places the analyzer is inferior and does not always
give correct analysis, for example equating ``VERB`` with ``ADV``. In
fact, there are various analyzer libraries providing functions for text
analysis. Some analyzers handle certain tasks better than others and
vice versa.

You need to make your pipeline more flexible and add a secondary
additional backup analyzer ``pymorphy2``, which will handle only
``NOUN`` tokens. The other parts of speech will be handled using
``pymystem3`` as before.

This way, by adding the possibility to use several analyzers, you can
improve the performance of the program, using all the best features of
each analyzer.

Stage 5.2. Introduce ``OpenCorporaTagConverter`` abstraction for ``pymorphy2`` tags
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before adding ``pymorphy2`` analyzer support, it is necessary to define
a converter which will convert the ``pymorphy2`` tags into the UD format
we are working with.
The ``lab_6_pipeline.pipeline.OpenCorporaTagConverter``
class should inherit :py:class:`core_utils.article.ud.TagConverter`
and use its methods.

The ``lab_6_pipeline.pipeline.OpenCorporaTagConverter`` instance
should be initialised with path to the tag mappings file.
You need to define tag mappings in the JSON
format under the ``lab_6_pipeline/data`` directory. Again, see
:ref:`ud-format-label` and :ref:`ud-mapping-label` for more information
on the UD format and its mapping with other formats.

.. note:: JSON file with ``pymorphy2`` tag mappings should be named
          ``opencorpora_tags_mapping.json``.

Implement ``lab_6_pipeline.pipeline.OpenCorporaTagConverter.convert_pos`` and
``lab_6_pipeline.pipeline.OpenCorporaTagConverter.convert_morphological_tags``
methods.

.. note:: Both methods require special ``tags`` parameter of the
          :py:class:`core_utils.article.ud.OpencorporaTagProtocol` type.
          When you analyse each token using
          ``pymorphy2`` you get the result of analysis as the
          :py:class:`core_utils.article.ud.OpencorporaTagProtocol` token instance.
          Inspect this object to get all morphological information required.

.. note:: As we handle only ``NOUN`` tokens you have to parse ``gender``,
          ``number``, ``animacy`` and ``case`` tags in
          ``lab_6_pipeline.pipeline.OpenCorporaTagConverter.convert_morphological_tags``
          method.

Stage 5.3. Introduce ``AdvancedMorphologicalAnalysisPipeline`` with backup analyzer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you are done defining ``pymorphy2`` into UD format mappings and
relevant converter, it is right time to implement the
``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline``
class with ``pymorphy2`` as backup analyser and
``lab_6_pipeline.pipeline.OpenCorporaTagConverter``
as backup converter.

You need to redefine
``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline._process``
method as you are inheriting from the
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline` class.

.. note:: You also need to specify own initializer of this class to
          create two more attributes alongside with parent’s attributes:
          ``pymorphy2`` as the ``self._backup_analyzer`` attribute and
          ``lab_6_pipeline.pipeline.OpenCorporaTagConverter`` as the
          ``self._backup_tag_converter`` attribute. Keep in mind that both fields
          are to be used only when you are working with ``NOUN`` tokens inside the
          ``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline._process``
          pipeline method.

.. note:: ``pymystem3`` may define some words as NOUN, but when you use
          backup ``pymorphy2`` analyzer it may define the same words as not
          NOUN and even provide no analysis at all. In this case you should
          still use the result of backup ``pymorphy2`` analyzer.

Stage 5.4. Save the results of ``AdvancedMorphologicalAnalysisPipeline``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You will need to redefine
``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline.run``
method as you are inheriting from
the :py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline`
class and need to call :py:func:`core_utils.article.io.to_conllu`
function with different parameters to save result to the appropriate folder.
Call this function with the article instance you want to save text for.

.. attention:: ``include_morphological_tags`` and ``include_pymorphy_tags``
               parameters should be ``True``.

The function generates a file with a name ``N_full_conllu.conllu``,
where ``N`` is the index of your article in the ``tmp/articles``
directory.

.. note:: It is mandatory to save generated text to file in the
          ``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline.run``
          method.

Stage 6. Implement analytical pipeline ``POSFrequencyPipeline`` for statistics collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have just made several text processing pipelines with base and
advanced processing logic. However, this is only the beginning of your
linguistic research: you have the data and now need to start analyzing
it, gaining insights, understanding it and finding hidden meanings.
During this stage we will make a small pipeline that will compute
distribution of various parts of speech in our texts, visualize it and,
maybe, it will give better understanding of the text.

This is a sample result we are going to obtain:

.. figure:: ../docs/images/sample_visualization.png
   :alt: sample_visualization.png

Stage 6.1. Introduce ``POSFrequencyPipeline`` abstraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we are going to work with the ``pos_frequency_pipeline.py`` file and with
the :py:class:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline` class.
All code should be written in the
:py:func:`lab_6_pipeline.pos_frequency_pipeline.main` function.
The :py:class:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline`
is instantiated in the similar manner as the
:py:class:`lab_6_pipeline.pipeline.MorphologicalAnalysisPipeline` or
``lab_6_pipeline.pipeline.AdvancedMorphologicalAnalysisPipeline``:

.. code:: python

   corpus_manager = CorpusManager(...)
   ...
   pipeline = POSFrequencyPipeline(corpus_manager=corpus_manager)

Stage 6.2. Extending ``ConlluSentence`` to support calculating POS frequencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since you are going to calculate POS frequencies of the tokens, you will
need to get access to ``ConlluTokens`` in ``ConlluSentences``.
In order to do that, implement the
:py:meth:`lab_6_pipeline.pipeline.ConlluSentence.get_tokens` method.

Stage 6.3. Introduce functionality for parsing UD-formatted files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to work with ``.conllu`` files which have already been written
(e.g. ``N_full_conllu.conllu``), you need not only be able to open those
files, but also to represent information from them using abstractions
you have previously written that are responsible for representing
information from ``.conllu`` files in your program. That is for example,
:py:class:`core_utils.article.article.Article` abstraction.

You need to implement :py:func:`lab_6_pipeline.pos_frequency_pipeline.from_conllu`
function that reads the information from
the ``.conllu`` file into the program and populates the
:py:class:`core_utils.article.article.Article`
abstraction with all information from the source file.

The function takes path to the article requested and optionally an
instance of :py:class:`core_utils.article.article.Article`.
Function reads and extracts all ``.conllu`` processing information
from relevant file and fills new
:py:class:`core_utils.article.article.Article` instance,
if no instance provided, or fills
:py:class:`core_utils.article.article.Article` instance
provided within the ``article`` param.

.. hint:: Inspect ``core_utils/article/ud.py`` module for service
          functionality that can be helpful in current task, especially
          :py:func:`core_utils.article.ud.extract_sentences_from_raw_conllu` function.

Stage 6.4. Implement core logic of ``POSFrequencyPipeline``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. important:: **Stages 0-6.4** are required to get the **mark 10**.

The :py:class:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline`
is executed with the same interface method
:py:meth:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline.run`
that you need to implement.

Once executed,
:py:meth:`lab_6_pipeline.pos_frequency_pipeline.POSFrequencyPipeline.run`:

1. Iterates through the available articles taken from
   :py:class:`lab_6_pipeline.pipeline.CorpusManager`.
2. Reads each file (any ``.conllu`` file type can be read, as each has POS info).
3. Calculates frequencies of each part of speech.
4. Writes them to the meta file.
5. Visualizes frequencies in a form of images with names following this
   convention: ``N_image.png``.

.. note:: It is mandatory to get articles with the
          :py:meth:`lab_6_pipeline.pipeline.CorpusManager.get_articles` method.

.. note:: It is mandatory to use :py:meth:`core_utils.article.article.Article.get_file_path`,
          :py:meth:`core_utils.article.article.Article.set_pos_info` methods and
          :py:func:`core_utils.article.io.to_meta`,
          :py:func:`core_utils.article.io.from_meta` functions.

.. note:: You have to create ``EmptyFileError`` exception class and to
          raise it when an article file is empty.

.. note:: Make sure that resulting meta files are valid: they must
          contain no more than one dictionary-line object.

.. hint:: To speedup ``pymystem3`` for processing large texts you should
          delete all line breaks. You can do it with regular expressions.

For visualization, you need to use :py:func:`core_utils.visualizer.visualize`
function.

Sample usage:

.. code:: python

   visualize(article=article, path_to_save=ASSETS_PATH / '1_image.png')
