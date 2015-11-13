#!/usr/bin/python3

#    This file is part of parsenlp.
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

import json
import ad
from ad.admath import *
import re

try:
	import pyipopt
except:
	print('Warning: pyipopt not found, defined problems can not be solved using json2ipopt.Problem.solve(), try installing pyipopt from https://github.com/xuy/pyipopt')
	print('')
	
	
class Problem(object):
	"""
	Class for defining a non-linear program
	"""
	def __init__(self,jsonstring=None):
		"""
		create an optimization problem from a jsonstring
		Arguments:
		jsonstring:		nlp definition in json format
		"""
		
		self.variables = []
		self.parameters = []
		self.constraints = []
		self.objective = None
		
		
		if jsonstring != None:
			# parse the json nlp definition .read().decode('utf-8')
			problem = json.loads(jsonstring)
			
			# create variables list
			for expression in problem['variables']:
				self.add_variable(expression)
			
			# add parameters to the variables list
			for expression in problem['parameters']:
				self.add_variable(expression)
			
			# add constraints to the constraint list
			for expression in problem['constraints']:
				self.add_constraint(expression)
			
			# set the objective
			self.set_objective(problem['objective'])
				
	def add_variable(self,expression):
		"""
		Adds a variable to the problem from a string expression
		Arguments:
		expression: string, variable name expression in python code with optional default value
		Example:
		nlp = parseipopt.problem()
		nlp.add_variable('T[j] for j in range(25)')
		nlp.add_variable('p[j] = 0.20 for j in range(24)')
		"""
		
		evalstr = self._parse_for_loop(expression)

		for expr in eval(evalstr):
			
			(lhs,rhs,eq) = self._parse_equation(expr)
			if rhs == '':
				self.variables.append(Variable(lhs.lstrip().rstrip()))
			else:
				self.variables.append(Variable(lhs.lstrip().rstrip(),lowerbound=eval(rhs),upperbound=eval(rhs)))
				
		
	def add_parameter(self,expression):
		"""
		alias of add_variable, parameters are treated as variables with equal lower and upper bound
		"""
		self.add_variable(expression)
		
		
	def add_constraint(self,expression):		
		"""
		Adds a constraint to the problem from a string expression
		Arguments:
		expression: string, equation or inequality expression in python code
		Example:
		nlp = parseipopt.problem()
		nlp.add_constraint('C*(T[j+1]-T[j])/dt = Q[j] - UA*(T[j]-Ta[j]) for j in range(24)')
		nlp.add_constraint('Tmin <= T[j] for j in range(24)')
		"""	
		
		evalstr = self._parse_for_loop(expression)
		
		for expr in eval(evalstr):	
			(lhs,rhs,type) = self._parse_equation(expr)
			
			if type =='':
				raise Exception('A constraint must contain an "=", "<=" or ">=" operator: ',expr)
			
			self.constraints.append(Constraint(lhs+'-('+rhs+')',type))
			
	def set_objective(self,expression):		
		"""
		sets the objective function of the problem from a string expression
		Arguments:
		expression: string, equation or inequality expression in python code
		Example:
		nlp = parseipopt.problem()
		nlp.set_objective('sum(p[j]*P[j] for j in range(24))')
		"""

		self.objective = Function(expression)
		
	def _parse_for_loop(self,expression):
		# look for the " for " keyword in the variable string
		# some logic needs to be added to avoid returning " for " in a sum
		
		forpos = expression.find(' for ')
		if forpos < 0:
			contentevalstr = '["'+expression+'"]'
			
		else:
			content = expression[:forpos+1]
			loop = expression[forpos:]
				
			# get the indices from the for loop
			indstr = []
			for sub in re.findall(r'for \w in',loop):
				indstr.append( sub[4:sub.find(' in')] )
			
			# replace occurrences of indstr with {}
			for i,index in enumerate(indstr):
				content = content.replace('['+index,'[{%s}'%i)
				content = content.replace(','+index,',{%s}'%i)
				
				content = content.replace(' '+index+' ',' {%s} '%i)
				
				contentevalstr = '["'+content+'".format('+','.join(indstr)+') '+loop+']' 
			
		return contentevalstr	
		
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
		
	# # callbacks
	# def gradient(self,x):
		# """
		# computes the objective function gradient
		
		# Arguments:
		# x:  list or numpy array of values with length equal to the number of variables
		# """
		
		# return self.objective.gradient(x);

	# def constraint(self,x):
		# """
		# computes all constraint functions values
		
		# Arguments:
		# x:  list or numpy array of values with length equal to the number of variables
		# """
		
		# result = []
		# for c in self._constraints:
			# result.append( c(x) )

		# return np.array(result,dtype=np.float)

	# def jacobian(self,x,flag):
		# """
		# computes the constraint jacobian matrix in the sparse form ipopt requires
		
		# Arguments:
		# x:     list or numpy array of values with length equal to the number of variables
		# flag:  boolean, when True the rows and columns of all always non zero entries are returned when False the values of these elements are returned
		# """
		
		# if flag:
			# row = []
			# col = []
			
			# for i,c in enumerate(self._constraints):
				# for j,g in enumerate(c.gradientexpression):
					# if g != '0':
						# row.append(i)
						# col.append(j)

			# return (np.array(row),np.array(col))
		# else:
			# val = []
			# for i,c in enumerate(self._constraints):
				# grad = c.gradient(x)
				# for j,g in enumerate(c.gradientexpression):
					# if g != '0':
						# val.append(grad[j])

			# return np.array(val,dtype=np.float)


	# # get functions
	# def get_variable_lowerbounds(self):
		# """
		# returns the lower bounds of all variables
		# """
		
		# values = []
		# for i in self._variables:
			# values.append(i.lowerbound)
		
		# return np.array(values)

	# def get_variable_upperbounds(self):
		# """
		# returns the upper bounds of all variables
		# """
		
		# values = []
		# for i in self._variables:
			# values.append(i.upperbound)
		
		# return np.array(values)

	# def get_constraint_lowerbounds(self):
		# """
		# returns the lower bounds of all constraints
		# """
		
		# values = []
		# for i in self._constraints:
			# values.append(i.lowerbound)
		
		# return np.array(values)

	# def get_constraint_upperbounds(self):
		# """
		# returns the upper bounds of all constraints
		# """
		
		# values = []
		# for i in self._constraints:
			# values.append(i.upperbound)
		
		# return np.array(values)

	# def get_values(self):
		# """
		# returns the values of all variables. These are initial values if the problem is not solved yet and the solution after problem.solve() is called
		# """
		
		# return np.array([v.value for v in self._variables])

	# def set_values(self,x):
		# """
		# sets the values of all variables, these will be used as initial values in a subsequent call to problem.solve()
		
		# Arguments:
		# x:  list or numpy.array with values, with length equal to the number of variables
		# """
		
		# for var,val in zip(self._variables,x):
			# var.value = val

	# # solve the problem using pyipopt
	# def solve(self,x0=None):
		# """
		# solves the problem using ipopt. The solution is set to variable.value
		
		# Arguments:
		# x0:  optional, list or numpy.array initial guess. If not supplied the current variable values will be used
		# """
		
		# if x0 == None:
			# x0 = self.get_values()
		# try:
			# pyipoptproblem = pyipopt.create(len(self._variables),
											# self.get_variable_lowerbounds(),
											# self.get_variable_upperbounds(),
											# len(self._constraints),
											# self.get_constraint_lowerbounds(),
											# self.get_constraint_upperbounds(),
											# len(self.jacobian(x0,False)),
											# 0,
											# self.objective,
											# self.gradient,
											# self.constraint,
											# self.jacobian)

			# x, zl, zu, constraint_multipliers, obj, status = pyipoptproblem.solve(x0)
			# self.set_values(x)
			# pyipoptproblem.close()
		# except:
			# raise Exception('pyipopt not found. You can try solving the problem using another solver using the parsenlp.Problem.objective, parsenlp.Problem.gradient, parsenlp.Problem.constraint, parsenlp.Problem.jacobian functions')
		


class Variable(object):
	def __init__(self,expression,lowerbound=-1e20,upperbound=1e20):
	
		self.expression = expression
		self.lowerbound = lowerbound
		self.upperbound = upperbound

		
class Function(object):
	def __init__(self,expression):
		self.expression = expression

	def set_values(self,_variables,_values):
		_advariables = []
		
		_vars = {}
		_expr = self.expression
		for _var,_val in zip(_variables,_values):
			_vars[_var.expression] = ad.adnumber(_val)
			_advariables.append(_vars[_var.expression])
			
			_expr = _expr.replace(_var.expression,'_vars["'+_var.expression+'"]')
		
		print(_vars)
		print(_expr)
		_adfunction = eval(_expr)

		return _adfunction,_advariables
	
	def gradient(self,var,val):
		_adfunction,_advariables = self.set_values(var,val)
		return _adfunction.gradient( _advariables )
		
	def hessian(self,var,val):
		_adfunction,_advariables = self.set_values(var,val)
		return _adfunction.hessian( _advariables )
		
	def __call__(self,var,val):
		_adfunction,_advariables = self.set_values(var,val)
		return _adfunction.real
	
	
class Constraint(Function):
	def __init__(self,expression,type):
		Function.__init__(self,expression)	
		if type == 'E':
			self.lowerbound = 0
			self.upperbound = 0
		elif type == 'L':
			self.lowerbound = -1e20
			self.upperbound = 0	
		elif type == 'G':
			self.lowerbound = 0
			self.upperbound = 1e20
			
