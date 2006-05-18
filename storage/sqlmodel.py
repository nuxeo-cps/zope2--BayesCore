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
""" Model definition."""
import os
from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from sqlobject import *
from sqlobject.main import SQLObjectNotFound

_marker = []


# ------------------------------------------------------------
# Schema
#
class Word(SQLObject):
    """Project table."""
    word_label              = StringCol(length=50, notNone=True)
    word_count              = IntCol(notNone=False, default=0)

class Category(SQLObject):
    category_label          = StringCol(length=50, notNone=True)
    category_title          = StringCol(length=100, notNone=False, default='')
    category_description    = StringCol(length=255, notNone=False, default='')

class Lang(SQLObject):
    lang_short_label        = StringCol(length=2, notNone=True)
    lang_label              = StringCol(length=255, notNone=False, default='')

# join to make a word belong to a category and a language
class CategorizedWord(SQLObject):
    category_id             = ForeignKey('Category')
    word_id                 = ForeignKey('Word')
    lang_id                 = ForeignKey('Lang')
    count                   = IntCol(notNone=False, default=0)

# ------------------------------------------------------------
# Functions
#
connection = None

def connect(connection_uri, debug=False, erase_if_exists=False):
    """Connect to the database uri, create tables if not present.

    erase_if_exists is only available for sqlite.
    """
    path = connection_uri.split(':')
    if path[0] == 'sqlite':
        if not path[1].startswith('///'):
            # got a relative path
            db_path = path[1][2:]
            db_filename = os.path.abspath(db_path)
            connection_uri = 'sqlite://' + db_filename
        if erase_if_exists:
            db_filename = connection_uri.split(':')[1][2:]
            if os.path.exists(db_filename):
                if debug:
                    print "Erasing %s" % db_filename
                os.unlink(db_filename)
    # connect to db
    global connection
    connection = dbconnection.TheURIOpener.connectionForURI(connection_uri)
    if debug:
        connection.debug = True
    create_tables()


def create_tables(if_not_exists=True):
    """Create tables.

    if_not_exists is False drop and create tables.
    """
    # setup schema if not present
    for cls in (Word, Category, Lang, CategorizedWord):
        cls.setConnection(connection)
        if not if_not_exists:
            cls.dropTable()
        cls.createTable(ifNotExists=if_not_exists)

def string_to_bool(text):
    """convert a string from a configuration file to a boolean."""
    if not isinstance(text, basestring):
        return not not text
    if text.lower() in ('off', 'no', 'false', '0'):
        return False
    else:
        return True

def conf_get(config, section, key, default=_marker):
    """Easy access to ConfigParser get.

    TODO: subclass ConfigParser"""
    try:
        val = config.get(section, key)
    except (NoSectionError, NoOptionError):
        if default is _marker:
            raise ValueError('not found %s: [%s] %s' % (config._conf_path,
                                                        section, key))
        val = default
    return val

def connect_using_conf(conf_path, db_name, debug=None):
    """Connect to the database defined in the configuration file conf_path
    in section conf_db."""
    config = ConfigParser()
    conf_abspath = os.path.abspath(conf_path)
    config.read(conf_abspath)
    config._conf_path = conf_abspath
    connection_uri = conf_get(config, db_name, 'connection_uri')
    if debug is None:
        debug = string_to_bool(conf_get(config, db_name, 'debug', 'False'))
    erase_if_exists = string_to_bool(
        conf_get(config, db_name, 'erase_if_exists', 'False'))
    # relative path must be interpreted from the configuration directory
    cur_path = os.path.curdir
    os.chdir(os.path.dirname(conf_abspath))
    connect(connection_uri, debug, erase_if_exists)
    os.chdir(cur_path)

def test_schema():
    """Create a tmp database to check the schema."""
    connect_using_conf('etc/sql.conf', 'bayes-test', debug=True)
    spam = Category(category_label='spam')
    word = Word(word_label= 'egg')
    lang = Lang(lang_short_label='fr', lang_label='français')

if __name__ == '__main__':
    test_schema()