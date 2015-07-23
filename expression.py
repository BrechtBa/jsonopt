#!/usr/bin/python3


#	This file is part of parsenlp.
#
#    parsenlp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    parsenlp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with parsenlp.  If not, see <http://www.gnu.org/licenses/>.

import re


class Expression:
	"""
	A class to parse mathematical expressions containing indexes and sums as commonly encountered in optimization problem definitions
	"""
	def __init__(self,string,indexnames,indexvalues=[]):
		"""
		Arguments:
		string: a string containing the expression
		indexnames: a list of strings containing indexes to replace
		indexvalues: a list of lists of numbers containing the values of the indexes

		Example:
		expression = Expression('A + B[i,j] + sum(sum(C[k]*D[i,j],k),i)', ['i','j','k'],[[0],[1],range(3)])
		expression.parse()
		"""
		self.string = string
		self.indexnames = indexnames
		self.indexvalues = indexvalues
		
	def parse(self,indexvalues=[]):
		"""
		return an expanded expression string
		"""
		if indexvalues != []:
			self.indexvalues = indexvalues
		if self.indexvalues == [] and self.indexnames != []:
			raise Exception('When indexes are present values must be supplied for parsing')

		string_expanded = self.string

		# parse sums
		sum_expression,sum_argument,sum_index = self.find_sum()
		
		if len(sum_expression)>0:
			for s,a,i in zip(sum_expression,sum_argument,sum_index):
				for indexname,indexvalue in zip(self.indexnames,self.indexvalues):
					if indexname == i:
						# create a string with the expand the sum 
						sum_expanded = re.sub( re.escape(s.string) ,'(' + '+'.join([self.replace_index(a.string,i,v) for v in indexvalue]) + ')' ,string_expanded)
						#create a new expression with the sum expanded and parse it
						string_expanded = Expression(sum_expanded,self.indexnames,self.indexvalues).parse()
						
		else:
			# there are no sub expressions
			for indexname,indexvalue in zip(self.indexnames,self.indexvalues):
				string_expanded = self.replace_index(string_expanded,indexname,indexvalue[0])
				
		# go one level up
		return string_expanded

	def replace_index(self,string,index,value):
		"""
		replaces the indexes in a string with values
		
		Arguments:
		string: a string with the expression containing indexes
		index: a string containing the index
		value: a number

		Example:
		expression.replace_index('A+B[j-1]+C[i,j]','j',3)
		# returns 'A+B[2]+C[i,3]'
		"""
		pre = ['[',',']
		delta = [-5,-4,-3,-2,-1,+1,+2,+3,+4,+5]

		for p in pre:
			for d in delta:
				string = re.sub(re.escape(p+index+'{:+.0f}'.format(d)),p+'{:.0f}'.format(value+d),string)

			string = re.sub(re.escape(p+index),p+'{:.0f}'.format(value),string)

		return string


	def find_sum(self):
		"""
		returns a list of the outer most sums in the expression
		"""
		
		expression = []
		argument = []
		index = []

		sum_code = 'sum'
		brace_open = '('
		brace_close = ')'

		start = self.string.find(sum_code)
		startarg = start + len(sum_code)
		
		# find the matching brace_close
		if start>=0:
			counter = 0
			for end,char in enumerate(self.string[startarg:]):
				if char == brace_open:
					counter = counter + 1
				if char == brace_close:    
					counter = counter - 1

				if counter==0:
					sum_string = self.string[start:startarg+end+1]
					
					
 					# find the last occurring ','
					for i,c in enumerate(reversed(sum_string)):
						if c==',':
							sum_index = sum_string[-i:-1]
							break

					expression = [Expression(sum_string,self.indexnames,self.indexvalues)]
					argument = [Expression(sum_string[len(sum_code)+1:-i-1],self.indexnames,self.indexvalues)]
					index = [sum_index]

					rest = Expression(self.string[startarg+end+1:],self.indexnames,self.indexvalues)
					rest_expression,rest_argument,rest_index = rest.find_sum()

					expression = expression + rest_expression
					argument = argument + rest_argument
					index = index + rest_index	
					break
					
			if counter != 0:
				raise Exception('Non matching delimiters: '+ expression[-1].string)

		return (expression,argument,index)
