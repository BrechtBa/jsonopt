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


class TestProblemSolution(unittest.TestCase):

	
	def test_default(self):
		with open('..//examples//json//hs071.json', 'r') as myfile:
			jsonstring=myfile.read()
			
		problem = jsonopt.Problem(jsonstring=jsonstring)
		
		try:
			problem.solve(verbosity=0)
		except:
			self.fail("solve() failed")
		
		
	def test_get_value(self):
		with open('..//examples//json//hs071.json', 'r') as myfile:
			jsonstring=myfile.read()
			
		best_known_x = np.array([0.99999999,  5.00000005,  1.44948976,  3.44948967])
		
		problem = jsonopt.Problem(jsonstring=jsonstring)
		problem.solve(verbosity=0)
		
		maxdelta = np.max(np.abs(problem.get_value('x')-best_known_x))
		self.assertLess(maxdelta,1e-3)
		
		
	def test_get_value_nd(self):
		problem = jsonopt.Problem()
		problem.add_parameter('p[i,j] = 0.20 if j==0 else 0.30 for i in range(24) for j in range(5)')
		
		maxdelta = np.max(np.abs( problem.get_value('p')-np.array([[0.20 if j==0 else 0.30 for j in range(5)] for i in range(24)]) ))
		self.assertEqual(maxdelta,0)

		
	def test_get_values(self):
		with open('..//examples//json//hs071.json', 'r') as myfile:
			jsonstring=myfile.read()
			
		best_known_x = np.array([0.99999999,  5.00000005,  1.44948976,  3.44948967])
			
		problem = jsonopt.Problem(jsonstring=jsonstring)
		problem.solve(verbosity=0)
		
		values = problem.get_values()
		maxdelta = np.max(np.abs(values['x']-best_known_x))
		
		self.assertEqual(values['A'],25)
		self.assertEqual(values['B'],40)
		self.assertEqual(values['C'],1)
		self.assertEqual(values['D'],5)
		self.assertLess(maxdelta,1e-3)
		
	def test_getitem(self):
		problem = jsonopt.Problem()
		problem.add_parameter('p[i,j] = 0.20 if j==0 else 0.30 for i in range(24) for j in range(5)')
		
		maxdelta = np.max(np.abs( problem.get_value('p')-np.array([[0.20 if j==0 else 0.30 for j in range(5)] for i in range(24)]) ))
		self.assertEqual(maxdelta,0)
		
	def test_getattr(self):
		problem = jsonopt.Problem()
		problem.add_parameter('p[i,j] = 0.20 if j==0 else 0.30 for i in range(24) for j in range(5)')
		
		maxdelta = np.max(np.abs( problem.get_value('p')-np.array([[0.20 if j==0 else 0.30 for j in range(5)] for i in range(24)]) ))
		self.assertEqual(maxdelta,0)
			
		
if __name__ == '__main__':
	unittest.main()