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

from __future__ import division
import json
import numpy as np
import pyomo.environ as pm
import pyomo.core.base.set_types
import re


class Problem:
	"""
	Class for defining a non-linear program
	"""
	
	validDomainExpressions = [v for v in dir(pyomo.core.base.set_types) if v[0].isupper()]
	
	def __init__(self,jsonstring=None):
		"""
		create an optimization problem from a jsonstring
		
		Parameters:
			jsonstring:		nlp definition in json format
		"""
		
		self.model = pm.ConcreteModel()
		
		self.variables = {}
		self.parameters = {}
		self.constraints = {}
		self.objective = None
		
		
		if jsonstring != None:
			# parse the json nlp definition .read().decode('utf-8')
			problem = json.loads(jsonstring)
			
			# create variables list
			for expression in problem['variables']:
				self.add_variable(expression)
			
			# add parameters to the variables list
			for expression in problem['parameters']:
				self.add_parameter(expression)
			
			# add constraints to the constraint list
			for expression in problem['constraints']:
				self.add_constraint(expression)
			
			# set the objective
			self.set_objective(problem['objective'])
				
				
	def add_variable(self,expression):
		"""
		Adds a variable to the problem from a string expression
		
		Parameters:
			expression: string, variable name expression in python code with optional default value
			
		Example:
			problem = jsonipopt.Problem()
			problem.add_variable('Reals x[j] for j in range(25)')
			problem.add_variable('Reals p[i,j] = 0.20 if j==0 else 0.30 for i in range(24) for j in range(5)')
		"""
		
		# get the domain of the variable
		splitexpression = expression.split(' ')
		domainexpr = splitexpression[0]
		if domainexpr in self.validDomainExpressions:
			domain = eval('pm.'+domainexpr)
		else:
			raise ValueError('The domain {} is not a valid domain. Valid domains are:\n{}'.format(domainexpr,self.validDomainExpressions))
		
		restexpression = ' '.join(splitexpression[1:])
		
		# parse the rest of the expression
		(name,indexvalue,initial) = self._parse_variable_or_parameter(restexpression)
		
		# add the variable
		if len(indexvalue)==0:
			if initial == []:
				setattr(self.model, name, pm.Var(domain=domain))
			else:
				setattr(self.model, name, pm.Var(domain=domain,initialize=initial))
		else:
			if initial == []:
				setattr(self.model, name, pm.Var(indexvalue,domain=domain))
			else:
				setattr(self.model, name, pm.Var(indexvalue,domain=domain,initialize=lambda model,*args: initial[args]))
		
		self.variables[name] = getattr(self.model, name)
		
		
	def add_parameter(self,expression):
		"""
		Adds a parameter to the problem from a string expression
		
		Parameters:
			expression: string, variable name expression in python code with a value
			
		Example:
			problem.add_parameter('A = 5')
			problem.add_parameter('p[i,j] = 0.20 if j==0 else 0.30 for i in range(24) for j in range(5)')
		"""
		
		# parse the rest of the expression
		(name,indexvalue,value) = self._parse_variable_or_parameter(expression)
		
		if value == []:
			raise ValueError('Parameters are required to have a value. {}'.format(expression))
		
		# add the parameter
		if len(indexvalue)==0:
			setattr(self.model, name, pm.Param(default=value))
		else:
			setattr(self.model, name, pm.Param(indexvalue,default=lambda model,*args: value[args]))
		
		self.parameters[name] = getattr(self.model, name)
		
		
		
	def add_constraint(self,expression,name=None):		
		"""
		Adds a constraint to the problem from a string expression
		
		Parameters:
			expression: string, equation or inequality expression in python code
			
		Example:
			problem.add_constraint('C*(T[j+1]-T[j])/dt = Q[j] - UA*(T[j]-Ta[j]) for j in range(24)')
			problem.add_constraint('Tmin <= T[j] for j in range(24)')
		"""	
		
		content,loop,indexlist,indexvalue = self._parse_for_array_creation(expression)
		
		# parse the equation type
		(lhs,rhs,type) = self._parse_equation(content)

		if type == 'E':
			pmtype = '=='
		elif type == 'G':
			pmtype = '>='
		elif type == 'L':
			pmtype = '<='			
		else:
			raise Exception('A constraint must contain an "=", "<=" or ">=" operator: {}'.format(expression))
		
		# add self.model to all variables and parameter in the expression
		pmexpression = lhs+pmtype+rhs
		
		# check the constraint name
		if name==None:
			name = 'unnamed_constraint{}'.format( len(self.constraints) )
		
		# create a vars dict
		pmvars = dict(self.variables)
		pmvars.update(self.parameters)

		# add the constraint
		if len(indexvalue)==0:
			setattr(self.model, name, pm.Constraint(expr=eval(pmexpression,pmvars)))
		else:
			def rule(model,*args):
				indexvars = {key:val for key,val in zip(indexlist,args)}
				pmvars.update(indexvars)
				return eval( pmexpression, pmvars )
				
			setattr(self.model, name, pm.Constraint(indexvalue,rule=rule))
		
		self.constraints[name] = getattr(self.model,name)
		
	def set_objective(self,expression):		
		"""
		sets the objective function of the problem from a string expression
		
		Parameters:
			expression: string, equation or inequality expression in python code
			
		Example:
			problem.set_objective('sum(p[j]*P[j] for j in range(24))')
		"""
		
		# create a vars dict
		pmvars = dict(self.variables)
		pmvars.update(self.parameters)
		
		def rule(model,*args):
			return eval( expression, pmvars )
				
		setattr(self.model, 'objective', pm.Objective(rule=rule))
		self.objective = getattr(self.model,'objective')
	
	
	def solve(self,solver='ipopt',solveroptions={},verbosity=1):
		"""
		solves the problem
		"""
		
		# parse inputs
		tee = False
		if verbosity>0:
			tee = True
			
		optimizer = pm.SolverFactory(solver)
		results = optimizer.solve(self.model,options=solveroptions,tee=tee)
	
	def get_value(self,name):
		"""
		gets the value of a variable or parameter
		
		Parameters:
			name:		string
		"""
		
		if name in self.variables:
			var = self.variables[name]
		elif name in self.parameters:
			var = self.parameters[name]
		else:
			raise KeyError('{} is not a variable or parameter'.format(name))
	
		if len(var)==1:
			return var.value
		else:
			dim = var.keys()[0]
			if isinstance( dim, int ):
				dim = [dim]
			else:
				dim = list(dim)
				
			for k in var.keys():
				if isinstance( k, int ):
					k = (k,)
				
				for i,v in enumerate(k):
					if v+1 > dim[i]:
						dim[i] = v+1
			

			value = np.zeros(dim)
			for key in var.keys():
				try:
					value[key] = var[key].value
				except:
					value[key] = var[key]
				
			return value
	
	def set_value(self,name,value):
		"""
		sets the value of a variable or parameter
		
		Parameters:
			name:		string
			value:		number, list, numpy.array
		
		Example:
			
		"""
	
	def get_values(self):
		"""
		returns the values of all variables and parameters in a dictionary
		"""
		values = {}
		for key in self.variables:
			values[key] = self.get_value(key)
		
		for key in self.parameters:
			values[key] = self.get_value(key)
			
		return values
	
	
	def __getitem__(self,name):
		return self.get_value(name)
			
	def __getattr__(self,name):
		return self.get_value(name)
	

	
	
	def _parse_variable_or_parameter(self,expression):	
		"""
		parses a variable or parameters into the required 
		
		Parameters:
			expression: string
			
		Returns:
			name: 			string
			indexvalue: 	list
			value: 			list
		"""

		# check if there is a 'for' statement and parse it
		(content,loop,indexlist,indexvalue) = self._parse_for_array_creation(expression)
		
		# check if the content contains a value
		(lhs,rhs,type) = self._parse_equation(content)
		
		# parse the variable name by removing brackets
		name,varindexlist = self._parse_indexed_expression(lhs)
			
		# parse the value
		value = []
		if rhs.lstrip().rstrip() != '':
			if len(indexvalue)==0:
				value = eval(rhs)
			else:
				value = np.array( eval('[ '*len(loop) + rhs + ' ' + ' ] '.join(loop[::-1]) + ' ]',vars()) )
		
		return (name,indexvalue,value)	

	def _parse_for_array_creation(self,expression):
		"""
		look for an array creating " for " keyword in a string
		
		some logic needs to be added to avoid returning " for " in a sum
		"""
		
		loop = []
		indexlist = []
		indexvalue = []
		
		# find (  ) statements
		bracepos = self._parse_matching_braces(expression,['(',')'])
		
		# find 'for  in' statements
		forpos = [p.start(0) for p in re.finditer('for .*? in ',expression)]
		
		# check if the for loop is inside braces and ignore it if so
		tempforpos = []
		for p in forpos:
			add = True
			for b in bracepos:
				if b[0] <= p and p <= b[1]:
					add = False
					break
			if add:
				tempforpos.append(p)
		
		forpos = tempforpos
		
		
		# split the expression
		if len(forpos) < 1:
			content = expression.rstrip().lstrip()
		else:
			content = expression[:forpos[0]].rstrip().lstrip()
			
			for p in forpos[::-1]:
				curloop = expression[p:].rstrip().lstrip()
				loop.append( curloop )
				
				curindex = re.findall('for (.*?) in', curloop)[0].rstrip().lstrip()
				indexlist.append( curindex )
				
				#indexvalue.append( eval( '['+ curindex + ' ' + curloop +']') )
			
				# remove the loop from the expression
				expression = expression[:p]
	
			# reverse the lists
			loop = loop[::-1]
			indexlist = indexlist[::-1]
			#indexvalue = indexvalue[::-1]
			
			# get the indexvalue
			indexvalue = eval( '[('+ ','.join(indexlist) + ')' + ' '.join(loop) +']')
				
		return content,loop,indexlist,indexvalue
		
	def _parse_indexed_expression(self,expression):
		"""
		parse and indexed expression into the variable and a list of indices
		
		Parameters:
			expression:		string, the expression
			
		Returns:
			variable: 		string, the variable which is indexed
			indexlist:		list, a list of index strings
		"""
		
		left_bracket = expression.find('[')
		right_bracket = expression.find(']')
		if left_bracket > -1:
			variable = expression[:left_bracket].lstrip().rstrip()
			indexlist = [i.lstrip().rstrip() for i in expression[left_bracket+1:right_bracket].split(',')]
		else:
			variable = expression.lstrip().rstrip()
			indexlist = []
		
		return (variable,indexlist)
	
		
	def _parse_equation(self,expression):
		eqpos = expression.find('=')
		gepos = expression.find('>=')
		lepos = expression.find('<=')
		
		if gepos > 0:
			lhs = expression[:gepos]
			rhs = expression[gepos+2:]
			type = 'G'
		elif lepos > 0:
			lhs = expression[:lepos]
			rhs = expression[lepos+2:]
			type = 'L'
		elif eqpos > 0:
			lhs = expression[:eqpos]
			rhs = expression[eqpos+1:]
			type = 'E'
		else:
			lhs = expression
			rhs = ''
			type = ''
			
		return (lhs,rhs,type)	
		
		
	def _parse_matching_braces(self,expression,braces):
		"""
		finds the matching braces or brackets in a string
		
		Parameters:
			expression: 	string, the expression to find braces in
			braces: 		list with 2 strings, starting and ending brace
		
		Returns:
			pairs:			list, with pairs lists
		"""
		
		openpos = [p.start(0) for p in re.finditer(re.escape(braces[0]),expression)]
		closepos = [p.start(0) for p in re.finditer(re.escape(braces[1]),expression)]
		
		openclosepos = [p.start(0) for p in re.finditer(re.escape(braces[0])+'|'+re.escape(braces[1]),expression)]
		
		pairs = []
		for i,o in enumerate(openclosepos):
			if o in openpos:
				num_open = 0
				num_close = 0
				
				for c in openclosepos[i:]:
					if c in openpos:
						num_open = num_open+1
					if c in closepos:
						num_close = num_close+1
						
					if num_open == num_close:
						pairs.append([o,c])
						break
		
		return pairs
		
