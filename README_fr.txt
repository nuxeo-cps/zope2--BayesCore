BayesCore
_________

:Revision: $Id$
:Author: Tarek Ziadé

BayesCore est un moteur bayésien spécialisé dans le traitement des
mails. Chaque message est d'abord pré-traité, puis classifié en fonction
d'une liste de thèmes. La base bayesienne est stockée dans une base SQL.

Pré-traitement des messages
===========================

Ce traitement est spécifique à la langue du message, en fabriquant une liste
des `lèmes`_, puis en applicant un `stemming`_ avec `pystemmer`_, qui
est une interface vers l'outil de stemming Snowball.

Certains mots sont également supprimés, par le biais d'une liste noire
et par un nombre minimum de lettres par mots.

Si la langue n'est pas disponible, le stemming et le filtrage des mots
ne sont pas effectués, sauf pour la qualification par nombres de lettres.

Les lèmes obtenus sont stockés dans une base de données et participent
à l'aprentissage.

Classification
==============

L'algorithme du moteur `Reverend`_, repris par BayesCore, est appliqué
aux messages, qui sont classifiés par ce biais. Cet algorithme
est repris et refactoré, pour intégrer des ajustements bayesiens,
et proposer un système de pluggable backend.

Stockage SQL
============

Le stockage des mots est effectué par un backend MySQL,
dans trois tables:

- WORD
- LANG
- CATEGORY

structure de WORD::

    nom champ           type
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

structure de LANG::

    nom champ       type
    _______________________________
    key             varchar(2)
    label           varchar

structure de CATEGORY::

    nom champ       type
    _______________________________
    key             integer
    title           varchar
    description     varchar

Si le volume de WORD devient important, et si une indexation
sql par le champ lang ne suffit plus à garantir des performances
optimales, un éclatement de la table par langues est envisageable.

Organisation du produit
=======================

Chaque composant de BayesCore est indépendant et peut être utilisé
dans un produit frontal pour proposer le service frontal de classification
au niveau du serveur CPS.

BayesCore manipule donc:

- un tokenizer, module de prétraitement des messages
- un classificateur
- un backend SQL, utilisé par le classificateur par le biais
  d'une abstraction par interface.

BayesCore est un composant Zope 3.

Définitions
===========

_`lèmes`: Le lemme (ou encore lexie) est l'unité autonome constituante du
lexique d'une langue. Dans le vocabulaire courant, on parlera plus souvent
de mot, notion qui, cependant, manque de clarté. On construit des énoncés
avec des lemmes, les lemmes sont faits de morphèmes. (wikipedia)

_`stemming`: A stemmer is a computer program or algorithm which determines
a stem form of a given inflected (or, sometimes, derived) word form?generally
a written word form. The stem need not be identical to the morphological
root of the word; it is usually sufficient that related words map to the
same stem, even if this stem is not in itself a valid root.

.. _`Reverend`: http://www.divmod.org/projects/reverend
.. _`pystemmer`: http://sourceforge.net/projects/pystemmer/