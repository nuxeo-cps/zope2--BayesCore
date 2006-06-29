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
from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.Length import Length
from interfaces import IBayesStorage
from register import registerStorageClass

class ZODBBayesStorage(Persistent):

    implements(IBayesStorage)

    def __init__(self, parameters=None):
        self._categories = OOBTree()
        self._languages = OOBTree()
        self._words = OOBTree() # keys are languages, values are Count instances
        self.parameters = parameters

    @classmethod
    def getStorageType(cls):
        """ tells what type of storage it is """
        return 'zodb'

    #
    # categories
    #

    def listCategories(self):
        """Iterate over categories keys"""
        return self._categories.iterkeys()

    def addCategory(self, name, title, description=''):
        """Give the name of the filter"""
        if self._categories.get(name) != (title, description):
            # ZODB optim: do not write if nothing to change
            self._categories[name] = (title, description)

    def getCategory(self, name):
        """Get category infos"""
        return self._categories[name]

    def delCategory(self, name):
        """Remove a category and clean words count for this category"""
        del self._categories[name]
        for word in self._words:
            self.delWord(word, name)

    #
    # langs
    #

    def listLanguages(self):
        """Iterate over languages keys"""
        return self._languages.iterkeys()

    def addLanguage(self, code, label):
        """Add a language"""
        if self._languages.get(code) != label:
            # ZODB optim: do not write if nothing to change
            self._languages[code] = label

    def getLanguage(self, code):
        """Get language infos"""
        return self._languages[code]

    def delLanguage(self, code):
        """Remove a language and corresponding word counts"""
        del self._languages[code]
        for word, counts_by_language in self._words.iteritems():
            if code in counts_by_language:
                del counts_by_language[code]

    #
    # words
    #

    def listWords(self, language=None, complete=False):
        """List all words, filtered by language if any"""
        if language is None:
            # should do some kind of aggregation between languages bu this is a
            # YAGNI
            raise NotImplementedError('yet')

        return self._listWordsForLanguage(language, complete)

    def _listWordsForLanguage(self, language, complete=False):
        """List all words, filtered by language"""
        for word, counts_by_language in self._words.iteritems():
            counts = counts_by_language.get(language, None)
            if counts is None:
                continue
            if complete:
                # BBB: YAGNI: the language tuple is useless
                # BBB: this structure is overcomplicated and should get
                # simplified
                yield (word, ((language,), counts.to_dict(),
                              counts.total_counts()))
            else:
                # YAGNI: the not complete case is probably useless as well
                yield word

    def addWord(self, word, language, categories=()):
        """Add a word and count it"""
        # ensure the language is already registered
        self._languages.setdefault(language, '')

        counts_by_languages = self._words.get(word, None)
        if counts_by_languages is None:
            counts_by_languages = self._words[word] = OOBTree()

        counts = counts_by_languages.get(language, None)
        if counts is None:
            counts = counts_by_languages[language] = Count()

        for category in _tuplify(categories):
            # ensure the category is already registered
            self._categories.setdefault(category, ('', ''))
            # do the actual count
            counts.increment(category)

    def getWord(self, word, language=None):
        """Get word info"""
        # YAGNI
        raise NotImplementedError('yet')

    def delWord(self, word, categories=None, language=None):
        """Remove categories for a given language if any

        If no language is specified, clean a languages for the given word
        """
        if language is None:
            # compute a copy of the list of languages to clean to avoid
            # modifying the "length" of a bucket while iterating on its content
            languages = tuple(self._words.get(word, {}).keys())
            for language in languages:
                self._delWordForLanguage(word, language, categories)
        else:
            self._delWordForLanguage(word, language, categories)

    def _delWordForLanguage(self, word, language, categories=None):
        """Remove categories for a given language

        Return True if the counts object is empty and hould be cleaned later on
        WARNING: this does not update the self._categories BTree
        """
        counts_by_language = self._words.get(word, {})
        if categories is None:
            # get rid of the whole count object
            if language in counts_by_language:
                del counts_by_language[language]

        else:
            # clean only the requested categories
            categories = _tuplify(categories)
            counts = counts_by_language.get(language, None)
            if counts is None:
                return
            for category in categories:
                del counts[category]
            # get rid of empty count objects
            if not counts:
                del counts_by_language[language]

    def wordCount(self, category=None, language=None):
        """Sum counts for all words matching category and language if given"""
        i = 0
        if language is not None:
            languages = (language,)
        for counts_by_language in self._words.itervalues():
            if language is None:
                # if no language given, then count all
                languages = counts_by_language.keys()
            for l in languages:
                counts = counts_by_language.get(l, None)
                if counts is None:
                    continue
                if category is None:
                    # if no category given, then count all
                    i += counts.total_counts()
                else:
                    i += counts.get(category, lambda:0)()

        return i

registerStorageClass(ZODBBayesStorage)

_marker = object()

class Count(Persistent):
    """Hold the counts for a given word in a given language

    This implementation relies upon Length objects to better handle conflict
    resolution.

    This implementation uses delegation instead of inheritance to avoid a wierd
    bug of btrees loosing their 'total_counts' attribute.
    """

    def __init__(self):
        self._btree = OOBTree()
        self.total_counts = Length()

    def __nonzero__(self):
        return bool(self.total_counts())

    def get(self, key, default=_marker):
        return self._btree.get(key, default)

    def increment(self, category):
        cat_count = self._btree.get(category, None)
        if cat_count is None:
            cat_count = self._btree[category] = Length()
        cat_count.change(1)
        self.total_counts.change(1)

    def __delitem__(self, category):
        cat_count = self._btree.get(category, None)
        if cat_count is not None:
            self.total_counts.change(-cat_count())
            del self._btree[category]

    def to_dict(self):
        """Make a dictionary copy of self

        Length instances are converted to their integer conterparts
        """
        return dict((cat, cat_count())
                    for cat, cat_count in self._btree.iteritems())

def _tuplify(element):
    if not isinstance(element, tuple):
        if isinstance(element, list):
            return tuple(element)
        else:
            return (element,)
    return element
