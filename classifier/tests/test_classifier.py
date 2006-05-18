#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2006 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#"
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
import unittest
import doctest
import os

from Products.BayesCore.classifier.classifier import BayesClassifier
from Products.BayesCore.tokenizer.filters import AllFilters
from Products.BayesCore.storage.zodb import ZODBBayesStorage

current_dir = os.path.dirname(__file__)

class TestClassifier(unittest.TestCase):

    def _getFileContent(self, filename):
        file = os.path.join(current_dir, filename)
        return open(file).read()

    def testSpamNoSPam(self):
        backend = ZODBBayesStorage()
        tokenizer = AllFilters()
        classifier = BayesClassifier('en', backend, tokenizer)

        classifier.learn(self._getFileContent('spam_sample.txt'), 'spam')
        classifier.learn(self._getFileContent('nospam_sample.txt'), 'nospam')

        res = list(classifier.guess(self._getFileContent('spam_to_guess.txt')))
        self.assertEquals(res[0][0], 'spam')

        res = list(classifier.guess(
                   self._getFileContent('no_spam_to_guess.txt')))
        self.assertEquals(res[0][0], 'nospam')

def test_suite():
    suites = [unittest.makeSuite(TestClassifier)]
    options = doctest.ELLIPSIS
    suites.append(doctest.DocFileTest('../classifier.txt',
                                      optionflags=doctest.ELLIPSIS))

    return unittest.TestSuite(suites)

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')
