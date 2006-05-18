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
import os
from zope.interface import implements
from interfaces import ITextTransform

__all__ =  ['applyFilter', 'applyFilters', 'AllFilters']

filters = {}

def registerFilter(filter_object):
    global filters
    if ITextTransform.providedBy(filter_object):
        filters[filter_object.getName()] = filter_object

def applyFilter(name, text, options):
    return filters[name].transform(text, options)

def applyFilters(names, text, options):
    for name in names:
        text = applyFilter(name, text, options)
    return text

class AllFilters(object):

    implements(ITextTransform)
    name = 'allfilters'

    def getName(self):
        return self.name

    def transform(self, text, options):
        tokenizers = ('splitter', 'stopwords', 'normalizer', 'stemmer')
        return applyFilters(tokenizers, text, options)

class TextSplitter(object):

    implements(ITextTransform)
    name = 'splitter'

    char_list = ',;:/\'"#?!.-=+_`|()[]{}<>~&§%'

    def getName(self):
        return self.name

    def _cleanChar(self, char):
        """ XXX at this time, we'll just use a small
            black list we'll see later on adding a real normalizer
            for each language that does all this in one pass
        """
        if char not in self.char_list:
            return char
        return ' '

    def transform(self, text, options):
        # removing unwanted character

        try:
            from zopyx.txng3.splitter import Splitter
            zopyx = True
        except ImportError:
            zopyx = False

        if zopyx:
            if 'treshold' in options:
                return Splitter(singlechar=0).split(text)
            else:
                return Splitter().split(text)

        text = ''.join([self._cleanChar(char) for char in text])
        result = text.split()

        if 'treshold' in options:
            treshold = options['treshold']
            return [word.lower() for word in result
                    if len(word) >= treshold]
        else:
            return [word.lower() for word in result]

registerFilter(TextSplitter())

class StopWords(object):

    implements(ITextTransform)
    name = 'stopwords'

    def getName(self):
        return self.name

    def _getStopWords(self, lang=None):
        """ simple text file, but will
        probably move to a DB storage"""
        currentpath = os.path.dirname(__file__)
        basefilename = os.path.join(currentpath, 'stopwords.txt')
        if lang is not None:
            filename = os.path.join(currentpath, 'stopwords.%s.txt' % lang)
            if not os.path.exists(filename):
                filename = basefilename
        else:
            filename = basefilename

        return [word.strip() for word in open(filename).readlines()
                if not (word.startswith('#') or word.strip() == '')]

    def transform(self, text, options):
        if 'lang' not in options:
            return text

        if isinstance(text, unicode) or isinstance(text, str):
            text = text.split()

        lang = options['lang']
        stopwords = self._getStopWords(lang)
        return [word for word in text if word not in stopwords]

registerFilter(StopWords())

class Normalizer(object):

    implements(ITextTransform)
    name = 'normalizer'

    def getName(self):
        return self.name

    def _getNormalizedChars(self, lang=None):
        """ simple text file, but will
        probably move to a DB storage"""
        currentpath = os.path.dirname(__file__)
        basefilename = os.path.join(currentpath, 'normalized.txt')
        if lang is not None:
            filename = os.path.join(currentpath, 'normalized.%s.txt' % lang)
            if not os.path.exists(filename):
                filename = basefilename
        else:
            filename = basefilename

        words = [word.strip() for word in open(filename).readlines()
                 if not (word.startswith('#') or word.strip() == '')]

        result = {}
        for word in words:
            splited = word.split()
            result[splited[0]] = splited[1]
        return result

    def _normalize(self, word, normalizer):
        def normalized(car):
            if car in normalizer:
                return normalizer[car]
            else:
                return car
        normalized = [normalized(car) for car in word]
        return ''.join(normalized)

    def transform(self, text, options):
        if 'lang' not in options:
            return text

        if isinstance(text, unicode) or isinstance(text, str):
            text = text.split()

        lang = options['lang']
        table = self._getNormalizedChars(lang)
        try:
            from zopyx.txng3 import normalizer
            zopyx = True
        except ImportError:
            zopyx = False

        if not zopyx:
            return [self._normalize(word, table) for word in text]
        else:
            return normalizer.Normalizer(table.items()).normalize(text)

registerFilter(Normalizer())

class Stemmer(object):

    implements(ITextTransform)
    name = 'stemmer'
    charset = 'ISO-8859-15'

    def getName(self):
        return self.name

    def getStemmerLanguage(self, lang):
        # pystemmer uses its own lang codes
        # XXX get the real ones
        langs = {'dn': 'danish', 'dt':'dutch', 'en': 'english',
                 'fr': 'french', 'de': 'german', 'it': 'italian',
                 'nw': 'norwegian', 'pr': 'porter',
                 'pg': 'portuguese', 'ru': 'russian', 'sp': 'spanish',
                 'sw': 'swedish'}
        if lang in langs:
            return langs[lang]
        return None

    def transform(self, text, options):
        if 'lang' not in options:
            return text
        if 'charset' not in options:
            charset = self.charset
        else:
            charset = options['charset']

        if isinstance(text, str) or isinstance(text, unicode):
            text = text.split()

        def checktype(element):
            if isinstance(element, str):
                return element.decode(charset)
            return element

        text =  [checktype(element) for element in text]

        try:
            from zopyx.txng3 import stemmer
        except ImportError:
            # module not available
            return text

        lang = self.getStemmerLanguage(options['lang'])
        if lang not in stemmer.availableStemmers():
            return text

        stemmer = stemmer.Stemmer(lang)

        return stemmer.stem(text)

registerFilter(Stemmer())
