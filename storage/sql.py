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
from interfaces import IBayesStorage
from register import registerStorageClass
from sqlmodel import (Word, Category, Lang, CategorizedWord, create_tables,
                      connect_using_conf, connect)

from sqlobject.sqlbuilder import AND, OR

class SQLBayesStorage(object):

    implements(IBayesStorage)
    charset = 'ISO-8859-15'

    def __init__(self, conf_file=None, db_name='', if_not_exists=True,
                 parameters=None):
        self.conf_file = conf_file
        self.db_name = db_name
        self.if_not_exists = if_not_exists
        self.parameters = parameters
        if self._connect():
            self._verifyStructure()

    def _connect(self):
        if self.conf_file is not None:
            connect_using_conf(self.conf_file, self.db_name)
            return True
        elif self.parameters is not None:
            connect(self.parameters)
            return True
        return False

    def _verifyStructure(self):
        """ will create tables over the sql base if they don't exist
        """
        create_tables(self.if_not_exists)

    @classmethod
    def getStorageType(cls):
        """ tells what type of storage it is """
        return 'sql'

    #
    # categories
    #
    def listCategories(self):
        """ get categories list """
        return (category.category_label
                for category in Category.select())

    def addCategory(self, name, title, description=''):
        """ give the name of the filter """
        if self.getCategory(name) != None:
            return
        cat = Category(category_label=name, category_title=title,
                       category_description=description)
        cat.sync()

    def getCategory(self, name):
        """ get category infos """
        results = Category.select(Category.q.category_label==name)
        if results.count() == 0:
            return None
        return results[0].category_title, results[0].category_description

    def delCategory(self, name):
        """ remove a category """
        results = Category.select(Category.q.category_label==name)
        if results.count() == 0:
            return None
        results[0].destroySelf()

    #
    # langs
    #
    def listLanguages(self):
        """ list available languages """
        return (unicode(lang.lang_short_label) for lang in Lang.select())

    def addLanguage(self, code, label):
        """ add a language """
        if self.getLanguage(code) != None:
            return
        lang = Lang(lang_short_label=code, lang_label=label)
        lang.sync()

    def getLanguage(self, code):
        """ get language infos """
        results = Lang.select(Lang.q.lang_short_label==code)
        if results.count() == 0:
            return None
        return unicode(results[0].lang_label, self.charset)

    def delLanguage(self, code):
        """ remove a language """
        results = Lang.select(Lang.q.lang_short_label==code)
        if results.count() == 0:
            return None
        results[0].destroySelf()

    #
    # words
    #
    def listWords(self, language=None, complete=False):
        """ list all words, filtered by language if given """
        if language is not None:
            query = AND(CategorizedWord.q.word_id == Word.q.id,
                        CategorizedWord.q.lang_id == Lang.q.id,
                        Lang.q.lang_short_label == language)
            selection =  Word.select(query)

            # XXX see how to multiplejoin
            ids = []
            def _filter(word):
                if word.id not in ids:
                    ids.append(word.id)
                    return False
                return True
            selection = filter(_filter, selection)
        else:
            selection = Word.select()

        if not complete:
            return (word.word_label for word in selection)
        else:
            return ((word.word_label, self._reprWord(word))
                    for word in selection)

    def addWord(self, word, language, categories=()):
        """ add a word """
        categories = _tuplify(categories)
        language = _tuplify(language)

        # getting existing word
        selection = Word.select(Word.q.word_label==word)

        if selection.count() == 0:
            # new word, let's add it
            current_word = Word(word_label=word)
            word_count = 0
        else:
            # existing word, let's increment it
            current_word = selection[0]
            word_count = current_word.word_count

        # updating langs and categories if needed,
        # and the join
        word_id = current_word.id

        for lang in language:
            selection = Lang.select(Lang.q.lang_short_label==lang)
            if selection.count() == 0:
                current_lang = Lang(lang_short_label=lang)
                current_lang.sync()
            else:
                current_lang = selection[0]

            for cat in categories:
                selection = Category.select(Category.q.category_label==cat)
                if selection.count() == 0:
                    current_cat = Category(category_label=cat)
                    current_cat.sync()
                else:
                    current_cat = selection[0]

                # updating the join
                cat_id = current_cat.id
                lang_id = current_lang.id
                query = AND(CategorizedWord.q.word_id == word_id,
                            CategorizedWord.q.category_id == cat_id,
                            CategorizedWord.q.lang_id == lang_id)

                selection = CategorizedWord.select(query)

                if selection.count() == 0:
                    new_categorized = CategorizedWord(word_id=word_id,
                                                      lang_id=lang_id,
                                                      category_id=cat_id,
                                                      count=1)
                    new_categorized.sync()
                    current_word.word_count += 1
                else:
                    for categorized in selection:
                        categorized.count += 1
                        categorized.sync()
                        current_word.word_count += categorized.count

        # syncing now the word (for word count)
        current_word.sync()

    def _reprWord(self, word):
        # XXX ugly code, will do sql joins here later
        catwords = CategorizedWord.select(CategorizedWord.q.word_id==word.id)
        langs = []
        cats = {}
        for catword in catwords:
            lang = Lang.select(Lang.q.id==catword.lang_id)
            if lang.count() > 0:
                label = lang[0].lang_short_label
                if label not in langs:
                    langs.append(label)

            cat = Category.select(Category.q.id==catword.category_id)
            if cat.count() > 0:
                cat = cat[0]
                cats[cat.category_label] = int(catword.count)

        return tuple(langs), cats, int(word.word_count)

    def getWord(self, word, language=None):
        """ get word infos """
        # TODO: handle language
        results = Word.select(Word.q.word_label==word)
        if results.count() == 0:
            return None
        return self._reprWord(results[0])

    def delWord(self, word, categories=None, language=None):
        """Remove a word"""
        results = Word.select(Word.q.word_label==word)
        if results.count() == 0:
            return None
        word = results[0]

        # picking up categorized words to work with
        if categories is None:
            catwords = CategorizedWord.select(CategorizedWord.q.word_id==word.id)
        else:
            categories = _tuplify(categories)

            # pointing words in CategorizedWord
            selector = AND(CategorizedWord.q.word_id==word.id,
                           CategorizedWord.q.category_id == Category.q.id,
                           Category.q.category_label in categories)

            catwords = CategorizedWord.select(selector)

        # remove categorized words
        categories = []
        for catword in catwords:
            category_id = catword.category_id
            if category_id not in categories:
                categories.append(category_id)
            if catword.count == 1:
                catword.destroySelf()
            else:
                catword.count -= 1
                catword.sync()

        # remove empty categories
        for category in categories:
            current_cat = Category.select(Category.q.id==category)
            if current_cat.count() > 0:
                current_cat = current_cat[0]
                category_id = current_cat.id
                selector = CategorizedWord.q.category_id==category_id
                catwords = CategorizedWord.select(selector)
                if catwords.count() == 0:
                    current_cat.destroySelf()

        # removing word if none use it
        catwords = CategorizedWord.select(CategorizedWord.q.word_id==word.id)
        if catwords.count() == 0:
            word.destroySelf()

    def wordCount(self, category=None, language=None):
        if category is None:
            if language is None:
                return Word.select().count()
            else:
                raise NotImplementedError
        else:
            categories = _tuplify(category)

            # pointing words in CategorizedWord
            selector = (Category.q.id == CategorizedWord.q.category_id,
                        Category.q.category_label in categories)

            catwords = CategorizedWord.select()
            return int(sum([catword.count for catword in catwords]))

registerStorageClass(SQLBayesStorage)

def _tuplify(element):
    if not isinstance(element, tuple):
        if isinstance(element, list):
            return tuple(element)
        else:
            return (element,)
    return element
