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
import doctest
import unittest

def test_suite():
    options = doctest.ELLIPSIS
    tests = []

    try:
        from zopyx.txng3 import stemmer
    except ImportError:
        # module not available
        return unittest.TestSuite(tests)
 
    tests.append(doctest.DocFileTest('tokenizer.txt',
                                     optionflags=doctest.ELLIPSIS))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    import unittest
    unittest.main(defaultTest='test_suite')
