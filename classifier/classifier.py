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
"""Robinson-fisher method was taken from PopF
"""
import math
import operator
from zope.interface import implements
from interfaces import IBayesClassifier

class BayesClassifier(object):

    implements(IBayesClassifier)

    def __init__(self, language, backend, tokenizer, **options):
        self.language = language
        self.backend = backend
        self.tokenizer = tokenizer
        if options is None:
            self.options = {'lang': self.language}
        else:
            self.options = options
            self.options['lang'] = self.language

    def learn(self, data, category):
        """ learn data for a given category

        wich means: store words in categories
        """
        self.backend.addCategory(name=category, title=category)
        data = self.tokenizer.transform(data, self.options)
        for element in data:
            self.backend.addWord(element, self.language, category)

    def unlearn(self, data, category):
        """ ulearn data for a given category

        wich means: remove words from categories
        """
        data = self.tokenizer.transform(data, self.options)
        for element in data:
            self.backend.delWord(element, category)

    def guess(self, data):
        """ guess a category for a given data """
        options = {'lang': self.language}
        data = self.tokenizer.transform(data, self.options)

        # XXX this will be cached
        probabilities = self._buildWordProbabilities()
        res = {}
        for category_name in probabilities:
            category_probs = probabilities[category_name]
            p = self.getProbs(category_probs, data)
            if len(p) != 0:
                res[category_name] = self._robinsonFisher(p, category_name)
        res = res.items()
        res.sort(lambda x,y: cmp(y[1], x[1]))
        return res

    def getProbs(self, category_probs, words):
        """ extracts the probabilities of tokens in a message
        """
        probs = [(word, category_probs[word])
                 for word in words if word in category_probs]
        probs.sort(lambda x,y: cmp(y[1],x[1]))
        return probs[:2048]

    def _robinsonFisher(self, probs, ignore):
        """ computes the probability of a message being spam (Robinson-Fisher method)
            H = C-1( -2.ln(prod(p)), 2*n )
            S = C-1( -2.ln(prod(1-p)), 2*n )
            I = (1 + H - S) / 2
            Courtesy of http://christophe.delord.free.fr/en/index.html
        """
        def _chi2P(chi, df):
            """ return P(chisq >= chi, with df degree of freedom)

            df must be even
            """
            assert df & 1 == 0
            m = chi / 2.0
            sum = term = math.exp(-m)
            for i in range(1, df/2):
                term *= m/i
                sum += term
            return min(sum, 1.0)

        n = len(probs)
        try:
            mlog = math.log(reduce(operator.mul, map(lambda p: p[1], probs), 1.0))
            H = _chi2P(-2.0 * mlog, 2*n)
        except OverflowError:
            H = 0.0
        try:
            mlog = math.log(reduce(operator.mul, map(lambda p: 1.0-p[1], probs), 1.0))
            S = _chi2P(-2.0 * mlog, 2*n)
        except OverflowError:
            S = 0.0
        return (1 + H - S) / 2

    def corpusSize(self, language=None):
        return self.backend.wordCount(language=language)

    def categorySize(self, category, language=None):
        return self.backend.wordCount(category=category, language=language)

    def _buildWordProbabilities(self, language=None):
        probs = {}
        for cat in self.backend.listCategories():
            probs[cat] = self._buildCategoryWordProbabilities(cat, language)
        return probs

    def _buildCategoryWordProbabilities(self, category, language=None):
        """Merges corpora and computes probabilities

        XXX to be cached later (invalidation on word adding)
        """
        if language is None:
            language = self.language
        corpus_size = self.corpusSize(language)
        category_size = float(self.categorySize(category, language))
        them_count = float(max(corpus_size - category_size, 1))
        probabilities = {}
        words = self.backend.listWords(language, complete=True)

        for word in words:
            if category not in word[1][1].keys():
                continue

            word_count = float(word[1][2])
            if word_count == 0.0:
                continue

            cat_word_count = float(word[1][1][category])
            other_count = cat_word_count - word_count

            if category_size == 0:
                good_metric = 1.0
            else:
                good_metric = min(1.0, other_count/category_size)

            bad_metric = min(1.0, cat_word_count/them_count)

            f = bad_metric / (good_metric + bad_metric)

            # PROBABILITY_THRESHOLD
            if abs(f-0.5) >= 0.1 :
                # GOOD_PROB, BAD_PROB
                probabilities[word[0]] = max(0.0001, min(0.9999, f))

        return probabilities
