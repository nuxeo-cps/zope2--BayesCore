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

from zope.interface import Interface

class ICategoryStorage(Interface):

    def listCategories():
        """ get categories list """

    def addCategory(name, title, description=''):
        """ give the name of the filter """

    def getCategory(name):
        """ get category infos """

    def delCategory(name):
        """ remove a category """

class ILangStorage(Interface):

    def listLanguages():
        """ list available languages """

    def addLanguage(code, label):
        """ add a language """

    def getLanguage(code):
        """ get language infos """

    def delLanguage(code):
        """ remove a language """

class IWordStorage(Interface):

    def listWords(language=None, complete=False):
        """ list all words, filtered by language if given """

    def addWord(word, language, categories=()):
        """ add a word """

    def getWord(word):
        """ get word infos """

    def delWord(word, categories=None):
        """ remove a word """

    def wordCount(category=None, language=None):
        """ give the corpus size """

class IBayesStorage(ICategoryStorage, ILangStorage, IWordStorage):

    def getStorageType():
        """ tells what type of storage it is """
