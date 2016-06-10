#!/usr/bin/env/ python
################################################################################
#    Copyright 2016 Brecht Baeten
#    This file is part of jsonopt.
#
#    jsonopt is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    jsonopt is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with jsonopt.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import unittest

import numpy as np

import jsonopt

class TestStringParsing(unittest.TestCase):

    def test_parse_for_array_creation_no_loop(self):
        (content,loop,indexlist,indexvalue) = jsonopt.parse.for_array_creation('x ')
        self.assertEqual(content,'x')
        self.assertEqual(loop,[])
        self.assertEqual(indexlist,[])
        self.assertEqual(indexvalue,[])

    def test_parse_for_array_creation(self):
        (content,loop,indexlist,indexvalue) = jsonopt.parse.for_array_creation('x[j] for j in range(10)')
        self.assertEqual(content,'x[j]')
        self.assertEqual(loop,['for j in range(10)'])
        self.assertEqual(indexlist,['j'])
        self.assertEqual(indexvalue,range(10))
    
    def test_parse_for_array_creation_multi(self):
        (content,loop,indexlist,indexvalue) = jsonopt.parse.for_array_creation('x[i,j,k] for i in range(2) for j in range(3) for k in range(4)')
        self.assertEqual(content,'x[i,j,k]')
        self.assertEqual(loop,['for i in range(2)', 'for j in range(3)', 'for k in range(4)'])
        self.assertEqual(indexlist,['i','j','k'])
        self.assertEqual(indexvalue,[(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 1, 0), (0, 1, 1), (0, 1, 2), (0, 1, 3), (0, 2, 0), (0, 2, 1), (0, 2, 2), (0, 2, 3), (1, 0, 0), (1, 0, 1), (1, 0, 2), (1, 0, 3), (1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 2, 0), (1, 2, 1), (1, 2, 2), (1, 2, 3)]) 
    
    def test_parse_for_array_creation_with_sum(self):
        (content,loop,indexlist,indexvalue) = jsonopt.parse.for_array_creation('x[i,j] = sum(a+b for a in range(i) for b in range(j)) for i in range(2) for j in range(3)')
        self.assertEqual(content,'x[i,j] = sum(a+b for a in range(i) for b in range(j))')
        
    def test_parse_variable(self):
        (name,indexvalue,value)    = jsonopt.parse.variable('x[j] for j in range(10)')
        self.assertEqual(name,'x')
        self.assertEqual(indexvalue,range(10))
        self.assertEqual(value,[])

    def test_parse_variable_with_initial_value(self):
        (name,indexvalue,value)    = jsonopt.parse.variable('x[j]=2 for j in range(10)')
        self.assertEqual(name,'x')
        self.assertEqual(indexvalue,range(10))
        self.assertEqual(list(value),[2 for j in range(10)])
        
        
    def test_parse_matching_braces(self):
        pairs = jsonopt.parse.matching_braces('x[i,j] = sum(a+b for a in range(i) for b in range(j)) for i in range(2) for j in range(3)',['(',')'])
        self.assertEqual(pairs,[[12, 52], [31, 33], [49, 51], [68, 70], [86, 88]])
        
    def test_parse_indexed_expression(self):
        (variable,indexlist) = jsonopt.parse.indexed_expression('x [i , j ]')
        self.assertEqual(variable,'x')
        self.assertEqual(indexlist,['i','j'])
        
    def test_parse_indexed_expression_not_indexed(self):
        (variable,indexlist) = jsonopt.parse.indexed_expression('x')
        self.assertEqual(variable,'x')
        self.assertEqual(indexlist,[])
        
        
        
if __name__ == '__main__':
    unittest.main()