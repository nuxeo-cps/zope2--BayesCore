# -*- coding: iso-8859-15 -*-
# Copyright (c) 2006 Nuxeo SAS <http://nuxeo.com>
# Authors : Tarek Ziadé <tziade@nuxeo.com>
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
from zope.interface import implements
from persistent import Persistent, dict
from interfaces import IBayesStorage
from register import registerStorageClass

class ZODBBayesStorage(Persistent):

    implements(IBayesStorage)

    def __init__(self, parameters=None):
        self._categories = dict.PersistentDict()
        self._languages = dict.PersistentDict()
        self._words = dict.PersistentDict()
        self.parameters = parameters

    @classmethod
    def getStorageType(cls):
        """ tells what type of storage it is """
        return 'zodb'

    #
    # categories
    #
    def listCategories(self):
        """ get categories list """
        return (key for key in self._categories.keys())

    def addCategory(self, name, title, description=''):
        """ give the name of the filter """
        if self._categories.get(name) != (title, description):
            # ZODB optim: do not write if nothing to change
            self._categories[name] = (title, description)

    def getCategory(self, name):
        """ get category infos """
        return self._categories[name]

    def delCategory(self, name):
        """ remove a category """
        del self._categories[name]

    #
    # langs
    #
    def listLanguages(self):
        """ list available languages """
        return (key for key in self._languages.keys())

    def addLanguage(self, code, label):
        """ add a language """
        self._languages[code] = label

    def getLanguage(self, code):
        """ get language infos """
        return self._languages[code]

    def delLanguage(self, code):
        """ remove a language """
        del self._languages[code]

    #
    # words
    #
    def listWords(self, language=None, complete=False):
        """ list all words, filtered by language if given """
        if language is None:
            if complete:
                return ((key, word)
                        for key, word in self._words.items())
            else:
                return (key for key in self._words.keys())
        else:
            if complete:
                return ((key, word) for key, word in self._words.items()
                        if language in word[0])

            else:
                return (key for key, word in self._words.items()
                        if language in word[0])

    def addWord(self, word, language, categories=()):
        """ add a word """
        def _merge(tuple1, tuple2):
            for item in tuple2:
                if item not in tuple1:
                    tuple1 = tuple1 + (item, )
            return tuple1

        if word in self._words.keys(): # explicit keys() for zodb mappings
            langs, cats, count = self._words[word]
            langs = _merge(langs, _tuplify(language))
            for category in _tuplify(categories):

                if category in cats:
                    cats[category] = cats[category] + 1
                else:
                    cats[category] = 1

                count += 1
        else:
            langs = _tuplify(language)
            cats = {}
            count = 0
            for category in _tuplify(categories):
                cats[category] = 1
                count += 1

        self._words[word] = langs, cats, count

    def getWord(self, word):
        """ get word infos """
        return self._words[word]

    def delWord(self, word, categories=None):
        """ remove a category """
        if categories is None:
            del self._words[word]
        else:
            # will have to decrement here
            langs, cats, count = self._words[word]
            count -= 1
            cats = list(cats)
            for category in _tuplify(categories):
                if category in cats:
                    cats.remove(category)
            if count == 0:
                del self._words[word]
            else:
                self._words[word] = langs, tuple(cats), count

            # now we need to remove empty cats
            for category in _tuplify(categories):
                if (self.wordCount(category=category) == 0
                    and category in self._categories):
                    self.delCategory(category)

    def wordCount(self, category=None, language=None):
        words = self._words.values()

        if category is None:
            if language is None:
                return sum([word[2] for word in words])
            else:
                return sum([word[2] for word in words
                           if language in word[0]])
        else:
            if language is None:
                return sum([word[2] for word in words
                            if category in word[1]])
            else:
                return sum([word[2] for word in words
                            if category in word[1] and
                               language in word[0]])

registerStorageClass(ZODBBayesStorage)

def _tuplify(element):
    if not isinstance(element, tuple):
        if isinstance(element, list):
            return tuple(element)
        else:
            return (element,)
    return element
