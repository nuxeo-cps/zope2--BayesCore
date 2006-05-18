BayesCore
_________

:Revision: $Id$
:Author: Tarek Ziad�

BayesCore est un moteur bay�sien sp�cialis� dans le traitement des
mails. Chaque message est d'abord pr�-trait�, puis classifi� en fonction
d'une liste de th�mes. La base bayesienne est stock�e dans une base SQL.

Pr�-traitement des messages
===========================

Ce traitement est sp�cifique � la langue du message, en fabriquant une liste
des `l�mes`_, puis en applicant un `stemming`_ avec `pystemmer`_, qui
est une interface vers l'outil de stemming Snowball.

Certains mots sont �galement supprim�s, par le biais d'une liste noire
et par un nombre minimum de lettres par mots.

Si la langue n'est pas disponible, le stemming et le filtrage des mots
ne sont pas effectu�s, sauf pour la qualification par nombres de lettres.

Les l�mes obtenus sont stock�s dans une base de donn�es et participent
� l'aprentissage.

Classification
==============

L'algorithme du moteur `Reverend`_, repris par BayesCore, est appliqu�
aux messages, qui sont classifi�s par ce biais. Cet algorithme
est repris et refactor�, pour int�grer des ajustements bayesiens,
et proposer un syst�me de pluggable backend.

Stockage SQL
============

Le stockage des mots est effectu� par un backend MySQL,
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
sql par le champ lang ne suffit plus � garantir des performances
optimales, un �clatement de la table par langues est envisageable.

Organisation du produit
=======================

Chaque composant de BayesCore est ind�pendant et peut �tre utilis�
dans un produit frontal pour proposer le service frontal de classification
au niveau du serveur CPS.

BayesCore manipule donc:

- un tokenizer, module de pr�traitement des messages
- un classificateur
- un backend SQL, utilis� par le classificateur par le biais
  d'une abstraction par interface.

BayesCore est un composant Zope 3.

D�finitions
===========

_`l�mes`: Le lemme (ou encore lexie) est l'unit� autonome constituante du
lexique d'une langue. Dans le vocabulaire courant, on parlera plus souvent
de mot, notion qui, cependant, manque de clart�. On construit des �nonc�s
avec des lemmes, les lemmes sont faits de morph�mes. (wikipedia)

_`stemming`: A stemmer is a computer program or algorithm which determines
a stem form of a given inflected (or, sometimes, derived) word form?generally
a written word form. The stem need not be identical to the morphological
root of the word; it is usually sufficient that related words map to the
same stem, even if this stem is not in itself a valid root.

.. _`Reverend`: http://www.divmod.org/projects/reverend
.. _`pystemmer`: http://sourceforge.net/projects/pystemmer/