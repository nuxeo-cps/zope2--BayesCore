BayesCore
_________

:Revision: $Id$
:Author: Tarek Ziadé

BayesCore is a naive bayesian inference engine for textual data (such as email
messages). Each piece of text is preprocessed then classified according to a
list of classes (aka categories or tags) which can be seen as fuzzy boolean
variables. BayesCore uses a SQL storage.


Text pre-processing
===================

Text pre-processing is language aware by building the list of `lemmas`_ occuring
in a message by tokenizing and `stemming`_ it with `pystemmer`_. Meaningless
words are also filtered out according to some language specific blacklists.

If the language of the message is not supported by BayesCore components, no
stemming nor filtering occurs.

Les lèmes obtenus sont stockés dans une base de données et participent
à l'aprentissage.


Classification
==============

The inference engine `Reverend`_ is applied to the pre-processed data to guess
learn and guess the categories.  This engine is adapted to allow for pluggable
backends.


SQL Storage
===========

The following three SQL tables are used:

- WORD::

    field               type
    _______________________________
    key                 integer
    word                varchar(50)
    category_1          external key
    category_1_count    integer
    category 2          external key
    category_2_count    integer
    category 3          external key
    category 3_count    integer
    lang1               external key
    lang2               external key
    lang3               external key
    count               integer

- LANG::

    field           type
    _______________________________
    key             varchar(2)
    label           varchar

- CATEGORY::

    nom champ       type
    _______________________________
    key             integer
    title           varchar
    description     varchar

Package structure
=================

Components are independant of each-other and can thus be used in seperate
frontal products in CPS for instance.

BayesCore provides the following components:

- a tokenizer to preprocess the messages
- a classifier
- a SQL storage used by the classifier through a Zope3 interface


Definitions
===========

_`lemma`: A lemma or citation form is the canonical form of a lexeme. Lexeme
refers to the set of all the forms that have the same meaning, and lemma refers
to the particular form that is chosen by convention to represent the lexeme.
(Wikipedia).

_`stemming`: A stemmer is a computer program or algorithm which determines
a stem form of a given inflected (or, sometimes, derived) word form, generally
a written word form. The stem need not be identical to the morphological
root of the word; it is usually sufficient that related words map to the
same stem, even if this stem is not in itself a valid root.

.. _`Reverend`: http://www.divmod.org/projects/reverend
.. _`pystemmer`: http://sourceforge.net/projects/pystemmer/
