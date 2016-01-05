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
			lowerbound = None
			upperbound = None
		else:
			lowerbound = np.array(eval('[' + rhs + loop + ']'))
			upperbound = np.array(eval('[' + rhs + loop + ']'))
				
		
		# add the variable to the problem
		self.variables.append( Variable(self,name,indexvalue,lowerbound,upperbound) )
		
		
		# for expr in eval(evalstr):

			# print(expr)
			
			# (lhs,rhs,eq) = _parse_equation(expr)
			# #if rhs == '':
			# #	self.variables.append(Variable(lhs.lstrip().rstrip()))
			# #else:
			# #	self.variables.append(Variable(lhs.lstrip().rstrip(),lowerbound=eval(rhs),upperbound=eval(rhs)))
				
		
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
		
	def get_temp_values(self):
		val = []
		for var in self.variables:
			for i,index in enumerate(var.index):
				val.append( 0.5*var.lowerbound[i] + 0.5*var.upperbound[i] )
				
		return val
	
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
		


class Variable:
	def __init__(self,problem,expression,indexvalue,lowerbound=None,upperbound=None):
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
		
		# assign bounds
		if lowerbound == None:
			self.lowerbound = -1.0e-20*np.ones_like(self.index)
		else:
			self.lowerbound = lowerbound
		
		if upperbound == None:
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






		
# ###############################################################################
# # ObjectContainer                                                             #
# ###############################################################################
# class ObjectContainer:
	# """
	# Container class for objects with names to allow easy access
	# """
	# def __init__(self):
		# self.objects = {}
		
	# def _add(self,obj):
		# # check if it is an indexed variable
		# if isinstance(obj.name, str):
			# i = obj.name.find('[')
			# if  i>0:
				# var = obj.name[:i]
				# ind = obj.name[i+1:-1]
			
				# # create a dummy np array witch ranges to the maximum dimension
				# ind = tuple(int(i) for i in ind.split(','))
				# dim = [int(i)+1 for i in ind]
				# if var in self.objects:
					# for i,(s,d) in enumerate( zip( self.objects[var].shape,dim) ):
						# if s > d:
							# dim[i] = s
				# dim = tuple(dim)
				
				# temp = np.empty(dim,dtype=object)
				# if var in self.objects:
				
					# for i, v in np.ndenumerate(self.objects[var]):
						# temp[i] = v
					
				# # fill in the current index
				# temp[ind] = obj
				# self.objects[var] = temp

		# # either way add the full obj name to the dictionary so both outer indexing and string indexing is possible
		# self.objects[obj.name] = obj
			
	# def __getitem__(self,key):
		# return self.objects[key]
		
	# def keys(self):
		# return self.objects.keys()	
		
		
# ###############################################################################
# # Variable                                                                    #
# ###############################################################################
# class Variable:
	# def __init__(self,name,symvar,evalvar,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
	
		# if name.find('_x_') >=0:
			# raise Exception('"_x_" is not allowed in a variable name, {}'.format(name))
			
		# if name.find('_p_') >=0:
			# raise Exception('"_p_" is not allowed in a variable name, {}'.format(name))
	
		# self.name = name
		# self.lowerbound = lowerbound
		# self.upperbound = upperbound
		# self._symvar = symvar
		# self._evalvar = evalvar
		# if value==None:	
			# self.value = 0.5*self.lowerbound + 0.5*self.upperbound
		# else:
			# self.value = value

	# def set_lowerbound(self,value):
		# self.lowerbound = value
		
	# def set_upperbound(self,value):
		# self.upperbound = value
		
# ###############################################################################	
# # Function                                                                    #
# ###############################################################################
# class Function:
	# def __init__(self,string,variables,parameters,gradientdict=None):
		# """
		# defines a function to be used in the optimization problem

		# Arguments:
		# string:          string to represent the expression
		# variables:       list of parsenlp.Variable, optimization problem variables
		# parameters:      list of parsenlp.Parameter, optimization problem parameters
		# gradientdict:  optional, dictionary of strings which represent the nonzero derivatives with the variable name as key
		# """
		# self.variables = variables
		# self.parameters = parameters

		
		# self.expression = string
		# self.sympyexpression = self.name2sympy(self.expression)
		# self.evaluationstring = self.name2eval(self.expression)

		# # calculate gradient
		# if gradientdict==None:
			# self.gradientsympyexpression = self.calculate_gradient()
			# self.gradientexpression = []

			# for g in self.gradientsympyexpression:
				# self.gradientexpression.append( self.sympy2name(g) )

		# else:
			# self.gradientexpression = []
			# for v in self.variables:
				# if v.name in gradientdict:
					# self.gradientexpression.append(gradientdict[v.name])
				# else:
					# self.gradientexpression.append('0')
			
		# # calculate the evaluation string		
		# self.gradientevaluationstring = []
		# for g in self.gradientexpression:
			# self.gradientevaluationstring.append( self.name2eval( g ) )
				
		# self.gradientevaluationstring = 'np.array([' + ','.join(self.gradientevaluationstring) + '],dtype=np.float)'
		
	# def gradient2dictionary(self):
		# """
		# returns a dictionary containing the non zero derivative with the variable name as key 
		# """
		# dictionary = {}
		# for v,g in zip(self.variables,self.gradientexpression):
			# if g != '0':
				# dictionary[v.name] = g
		# return dictionary
		
	# def name2sympy(self,string):
		# """
		# replace variable and parameter names with sympy variables
		# """
		
		# sympyexpression = string
		# for p in self.parameters:
			# sympyexpression = sympyexpression.replace(p.name,str(p._symvar))
		# for v in self.variables:
			# sympyexpression = sympyexpression.replace(v.name,str(v._symvar))
			
		# return sympyexpression
	
	# def name2eval(self,string):
		# """
		# replace variable and parameter names with evaluation variables
		# """
		
		# specialfunctions = {'log(':'np.log(','exp(':'np.exp(','sin(':'np.sin(','cos(':'np.cos(','tan(':'np.tan('}

		# evaluationstring = string
		# for p in self.parameters:
			# evaluationstring = evaluationstring.replace(p.name,p._evalvar )
		# for v in self.variables:
			# evaluationstring = evaluationstring.replace(v.name,v._evalvar)
		
		# for f in specialfunctions:
			# evaluationstring = evaluationstring.replace(f,specialfunctions[f])
			
		# return evaluationstring
	
	# def sympy2name(self,sympyexpression):
		# """
		# replace sympy variables and parameters with variable names
		# """
		
		# expression = sympyexpression
		# # reversed so x34 get replaced before x3
		# for v in self.variables:
			# expression = expression.replace(str(v._symvar),v.name)
		# for p in reversed(self.parameters):
				# expression = expression.replace(str(p._symvar),p.name)
			
		# return expression
		
		
	# def calculate_gradient(self):
		# """
		# returns a list of strings which contain the derivatives to all variables with sympy names
		# """
		
		# gradientsympyexpression = []
		# for v in self.variables:
			# try:
				# gradientsympyexpression.append( str(sympy.diff(self.sympyexpression,v._symvar)) )
			# except:
				# raise Exception('Error while differentiating constraint: '+self.expression)
		# return gradientsympyexpression
		
	
	# def __call__(self,_x_):
		# """
		# return the function result
		# """
		# _p_ = np.array([p.value for p in self.parameters])
		# return eval(self.evaluationstring)


	# def gradient(self,_x_):
		# """
		# return the gradient result
		# """
		# _p_ = np.array([p.value for p in self.parameters])
		# return eval(self.gradientevaluationstring)

# ###############################################################################
# # Constraint                                                                  #
# ###############################################################################
# class Constraint(Function):
	# def __init__(self,string,variables,parameters,gradientdict=None,lowerbound=None,upperbound=None,name=''):
		# Function.__init__(self,string,variables,parameters,gradientdict=gradientdict)
		
		# if lowerbound == None and upperbound == None:
			# lowerbound = 0
			# upperbound = 0
		# elif lowerbound == None:
			# lowerbound = min(0,upperbound)
		# elif upperbound == None:
			# upperbound = max(0,lowerbound)

		# self.lowerbound = lowerbound
		# self.upperbound = upperbound
		# self.name = name

	# def set_lowerbound(self,value):
		# self.lowerbound = value

	# def set_upperbound(self,value):
		# self.upperbound = value

