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
import re

import numpy as np

import pyomo.environ as pm
import pyomo.core.base.set_types

import parse

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
		(name,indexvalue,initial) = parse.variable(restexpression)
		
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
		(name,indexvalue,value) = parse.variable(expression)
		
		if value == []:
			raise ValueError('Parameters are required to have a value. {}'.format(expression))
		
		# add the parameter
		if len(indexvalue)==0:
			setattr(self.model, name, pm.Param(default=value,mutable=True))
		else:
			setattr(self.model, name, pm.Param(indexvalue,default=lambda model,*args: value[args],mutable=True))
		
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
		
		content,loop,indexlist,indexvalue = parse.for_array_creation(expression)
		
		# parse the equation type
		(lhs,rhs,type) = parse.equation(content)

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
	
	def get_variable(self,name):
		"""
		gets a variable
		
		Parameters:
			name:		string
		"""
		if name in self.variables:
			var = self.variables[name]
		elif name in self.parameters:
			var = self.parameters[name]
		elif name == 'objective':
			var = self.objective
		else:
			raise KeyError('{} is not a variable or parameter or the objective'.format(name))
			
		return var
		
	def set_value(self,name,value):
		"""
		sets the value of a variable or parameter
		
		Parameters:
			name:		string, the variable name, this can be an indexed string
			value:		number, the value of the variable
		
		Example:
			problem.set_value('A',1)
			problem.set_value('x[3]',1)
		"""
		
		# check if the name is an indexed string
		(varname,indexlist) = parse.indexed_expression(name)
		var = self.get_variable(varname)
		
		if len(indexlist)==0:
			var.set_value(value)
		else:
			try:
				var[eval('(' + ','.join(indexlist) + ',)')].set_value(value)
			except:
				var[eval('(' + ','.join(indexlist) + ',)')].value = value

				
	def get_value(self,name):
		"""
		gets the value of a variable or parameter
		
		Parameters:
			name:		string
		"""
		
		var = self.get_variable(name)
	
		if len(var)==1:
			if var.__class__.__name__== 'SimpleObjective':
				return var.expr()
			else:
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
			
			
	def get_json_value(self,name):
		"""
		"""
		value = self.get_value(name)
		if type(value).__module__ == np.__name__:
			value = value.tolist()
				
		return json.dumps(value)
	
	def get_values(self):
		"""
		returns the values of all variables and parameters in a dictionary
		"""
		values = {}
		for key in self.variables:
			values[key] = self.get_value(key)
		
		for key in self.parameters:
			values[key] = self.get_value(key)
		
		values['objective'] = self.get_value('objective')
		
		return values
	
	def get_json_values(self):
		"""
		"""
		values = self.get_values()
		
		# convert arrays to lists
		for key in values:
			if type(values[key]).__module__ == np.__name__:
				values[key] = values[key].tolist()
				
		return json.dumps(values)
	
	
	def __getitem__(self,name):
		return self.get_value(name)
			
	def __getattr__(self,name):
		return self.get_value(name)
	