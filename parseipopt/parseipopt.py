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
import numpy as np
import ad
from ad.admath import *
import re

try:
	import pyipopt
except:
	print('Warning: pyipopt not found, defined problems can not be solved using json2ipopt.Problem.solve(), try installing pyipopt from https://github.com/xuy/pyipopt')
	print('')
	
	
class Problem:
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
		
		content,loop,indexlist,indexvalue = _parse_for_array_creation(expression)
		
		(lhs,rhs,eq) = _parse_equation(content)
		
		bracket = lhs.find('[')
		if bracket > -1:
			name = lhs[:bracket]
		else:
			name = lhs
			
		name = name.lstrip().rstrip()
		
		if rhs == '':
			lowerbound = []
			upperbound = []
		else:
			lowerbound = np.array(eval('[' + rhs + loop + ']'))
			upperbound = np.array(eval('[' + rhs + loop + ']'))
				
		# add the variable to the problem
		self.variables.append( Variable(self,name,indexvalue,lowerbound,upperbound) )
		
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
		
		content,loop,indexlist,indexvalue = _parse_for_array_creation(expression)
		
		(lhs,rhs,type) = _parse_equation(content)

		if type == '':
				raise Exception('A constraint must contain an "=", "<=" or ">=" operator: ',expr)
		
		if len(indexlist) > 0:
			index = indexlist[0];
			for val in indexvalue:
				expression = lhs+'-('+rhs+')'
				
				expression = expression.replace( '['+index,'['+str(val) )
				expression = expression.replace( '[ '+index,'[ '+str(val) )
				expression = expression.replace( ','+index,','+str(val) )
				expression = expression.replace( ', '+index,', '+str(val) )
				
				expression = expression.replace( index+']',str(val)+']' )
				expression = expression.replace( index+' ]',str(val)+' ]' )
				expression = expression.replace( index+',',str(val)+',' )
				expression = expression.replace( index+' ,',str(val)+' ,' )

				self.constraints.append( Constraint(self,expression,type) )
		else:
			expression = lhs+'-('+rhs+')'
			self.constraints.append( Constraint(self,expression,type) )
				
	def set_objective(self,expression):		
		"""
		sets the objective function of the problem from a string expression
		Arguments:
		expression: string, equation or inequality expression in python code
		Example:
		nlp = parseipopt.problem()
		nlp.set_objective('sum(p[j]*P[j] for j in range(24))')
		"""
		
		self.objective = Function(self,expression)
		
	def count_variables(self):
		val = 0;
		for var in self.variables:
			val += len(var.index)
			
		return val
	
	# callbacks
	def gradient(self,x):
		"""
		computes the objective function gradient
		
		Arguments:
		x:  list or numpy array of values with length equal to the number of variables
		"""
		
		return self.objective.gradient(x);

	def constraint(self,x):
		"""
		computes all constraint functions values
		
		Arguments:
		x:  list or numpy array of values with length equal to the number of variables
		"""
		
		result = []
		for c in self.constraints:
			result.append( c(x) )

		return np.array(result,dtype=np.float)

	def jacobian(self,x,flag):
		"""
		computes the constraint jacobian matrix in the sparse form ipopt requires
		
		Arguments:
		x:     list or numpy array of values with length equal to the number of variables
		flag:  boolean, when True the rows and columns of all non zero entries are returned when False the values of these elements are returned
		"""
		
		if flag:
			x_temp1 = np.random.random(len(x))
			x_temp2 = np.random.random(len(x))
			row = []
			col = []
			
			for i,c in enumerate(self.constraints):
				for j in c.nonzero_gradient_columns:
					row.append(i)
					col.append(j)

			return (np.array(row),np.array(col))
			
		else:
			val = []
			for i,c in enumerate(self.constraints):
				grad = c.gradient(x)
				for j in c.nonzero_gradient_columns:
					val.append(grad[j])

			return np.array(val,dtype=np.float)


	# get and set functions
	def get_values(self):
		"""
		returns the values of all variables. These are initial values if the problem is not solved yet and the solution after problem.solve() is called
		"""
		
		values = np.array([])
		for v in self.variables:
			values = np.append(values,v.value)
			
		return values
		
	def set_values(self,x):
		"""
		sets the values of all variables, these will be used as initial values in a subsequent call to problem.solve()
		
		Arguments:
		x:  numpy.array with values, with length equal to the number of variables
		"""
		
		for var in self.variables:
			var.value = x[var.index]
			
	def get_value_dict(self):
		"""
		returns the values of all variables. in a dictionary
		"""
		
		values = {}
		for v in self.variables:
			values[v.expression] = v.value
			
		return values
		
	def set_value_dict(self,d):
		"""
		sets the values of all variables, these will be used as initial values in a subsequent call to problem.solve()
		
		Arguments:
		d:  dictionary with variable expressions as keys and values as value, as generated by get_value_dict()
		"""
		
		for var in self.variables:
			var.value = d[var.expression]
	
	
	def get_variable_lowerbounds(self):
		"""
		returns the lower bounds of all variables
		"""
		
		values = np.array([])
		for v in self.variables:
			values = np.append(values,v.lowerbound)
		
		return values

	def get_variable_upperbounds(self):
		"""
		returns the upper bounds of all variables
		"""
		
		values = np.array([])
		for v in self.variables:
			values = np.append(values,v.upperbound)
		
		return values

	def get_constraint_lowerbounds(self):
		"""
		returns the lower bounds of all constraints
		"""
		
		values = np.array([])
		for c in self.constraints:
			values = np.append(values,c.lowerbound)
		
		return values

	def get_constraint_upperbounds(self):
		"""
		returns the upper bounds of all constraints
		"""
		
		values = np.array([])
		for c in self.constraints:
			values = np.append(values,c.upperbound)
		
		return values

			
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
		


class Variable:
	def __init__(self,problem,expression,indexvalue,lowerbound=[],upperbound=[]):
		"""
		Arguments:
		expression: string, 
		
		Example:
		Variable(nlp,'Pmax',())
		Variable(nlp,'P',(24,))
		Variable(nlp,'p',(24,),0.2*np.ones((24,)),0.2*np.ones((24,)))
		"""
		
		self.problem = problem
		
		self.expression = expression
		
		# assign indexes to each variable
		num = max(1,len(indexvalue))

		if len(self.problem.variables)==0:
			self.index =  np.arange(num)
		else:
			self.index = self.problem.variables[-1].index[-1] + np.arange(num) +1
		
		# assign values
		if len(lowerbound) != num and len(upperbound) != num:
			self.value = 0*np.ones_like(self.index)
		elif len(lowerbound) != num:
			self.value = upperbound
		elif len(upperbound) != num:
			self.value = lowerbound
		else:
			self.value = 0.5*lowerbound + 0.5*upperbound
			
			
		# assign bounds
		if len(lowerbound) != num:
			self.lowerbound = -1.0e-20*np.ones_like(self.index)
		else:
			self.lowerbound = lowerbound
		
		if len(upperbound) != num:
			self.upperbound = +1.0e-20*np.ones_like(self.index)
		else:
			self.upperbound = upperbound	

		
class Function:
	def __init__(self,problem,expression):
		self.problem = problem
		self.expression = expression

		# replace variable expressions with their _expressions
		
		self._expression = expression
		
		def callback(x):
			# parse x
			for var in self.problem.variables:
				if len(var.index) ==1:
					x_expression = 'x[{}]'.format(var.index[0])
				else:
					x_expression = '[' + ','.join(['x[{}]'.format(index) for index in var.index]) +']'
					
				exec(var.expression + '=' + x_expression, globals(), locals() )
				
			return eval(self._expression,globals(),locals())
		
		grad,hess = ad.gh(callback)
		
		self.call = callback
		self.grad = grad
		self.hess = hess
		
		self.nonzero_gradient_columns = self.get_nonzero_gradient_columns()
		
	def set_values(self,_variables,_values):
		_advariables = []
		
		_vars = {}
		_expr = self.expression
		for _var,_val in zip(_variables,_values):
			_vars[_var.expression] = ad.adnumber(_val)
			_advariables.append(_vars[_var.expression])
			
			_expr = _expr.replace(_var.expression,'_vars["'+_var.expression+'"]')
		
		_adfunction = eval(_expr)

		return _adfunction,_advariables
		
	def get_nonzero_gradient_columns(self):
	
		n = self.problem.count_variables()
		x1 = np.random.random(n)
		x2 = np.random.random(n)
		
		col = []

		for j, (g1,g2) in enumerate( zip(self.gradient(x1),self.gradient(x2)) ):
			if g1 != 0 and g2!= 0:
				col.append(j)
	
		return col
		
	def gradient(self,x):
		return self.grad(x)
		
	def hessian(self,x):
		return self.hess(x)
		
	def __call__(self,x):
		return self.call(x)
	
	
class Constraint(Function):
	def __init__(self,problem,expression,type):
		Function.__init__(self,problem,expression)	
		if type == 'E':
			self.lowerbound = 0
			self.upperbound = 0
		elif type == 'L':
			self.lowerbound = -1e20
			self.upperbound = 0	
		elif type == 'G':
			self.lowerbound = 0
			self.upperbound = 1e20
		

def _parse_for_array_creation(expression):
	# look for an array creating " for " keyword in a string
	# some logic needs to be added to avoid returning " for " in a sum
	
	forpos = expression.find(' for ')
	if forpos < 0:
		contentevalstr = '["'+expression+'"]'
		content = expression
		loop = ''
		indexlist = []
		indexvalue = []
	else:
		content = expression[:forpos+1]
		loop = expression[forpos:]
		
		# get the indices from the for loop
		indexlist = []
		for sub in re.findall(r'for \w in',loop):
			indexlist.append( sub[4:sub.find(' in')] )
		
		# get all possible values of the indices
		indexvalue = eval( '[('+ ','.join(indexlist) + ')' + loop +']')
			
		# replace occurrences of indstr with {}
		# evalcontent = content
		# for i,index in enumerate(evalind):
			# evalcontent = evalcontent.replace('['+index,'[{%s}'%i)
			# evalcontent = evalcontent.replace(','+index,',{%s}'%i)
			
			# evalcontent = evalcontent.replace(' '+index+' ',' {%s} '%i)
			
		# evalstr = '["'+evalcontent+'".format('+','.join(evalind)+') '+loop+']' 
		#,evalcontent,evalind,loop,content
	return content,loop,indexlist,indexvalue
	
	
def _parse_equation(expression):
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
