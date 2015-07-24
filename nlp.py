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

import numpy as np
import sympy
try:
	import pyipopt
except:
	print('Warning: pyipopt not found, defined problems can not be solved using parsenlp.Problem.solve(), try installing pyipopt from https://github.com/xuy/pyipopt')

class Problem:
	"""
	Class for defining a non-linear program
	"""
	def __init__(self):
		"""
		create an empty optimization problem
		"""
		
		self.variables = ObjectContainer()
		self._variables = []
		self.parameters = ObjectContainer()
		self._parameters = []
		self.constraints = ObjectContainer()
		self._constraints = []
		
		self.objective = None

	def add_variable(self,name,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
		"""
		adds a variable to the optimization problem
		
		Arguments:
		name:        string variable name used in the definition of constraints and objectives
		lowerbound:  optional, float variable lower bound
		upperbound:  optional, float variable upper bound
		value:       optional, float variable initial value
		
		Example:
		nlp = parsenlp.Problem()
		nlp.add_variable('x[0]')
		"""
		
		if value==None:
			value = 0.5*lowerbound + 0.5*upperbound

		symvar = sympy.Symbol( '_x{0}_'.format(len(self._variables)) )
		evalvar = '_x_[{0}]'.format(len(self._variables))
		self._variables.append( Variable(name,symvar,evalvar,lowerbound=lowerbound,upperbound=upperbound,value=value) )
		self.variables._add(self._variables[-1])
		
		return self._variables[-1]

	def add_parameter(self,name,value):
		"""
		adds a parameter to the optimization problem
		
		Arguments:
		name:   string parameter name used in the definition of constraints and objectives
		value:  float parameter value
		
		Example:
		nlp = parsenlp.Problem()
		nlp.add_parameter('C',5.0)
		"""
		
		symvar = sympy.Symbol( '_p{0}_'.format(len(self._parameters)) )
		evalvar = '_p_[{0}]'.format(len(self._parameters))
		self._parameters.append( Variable(name,symvar,evalvar,lowerbound=value,upperbound=value,value=value) )
		self.parameters._add(self._parameters[-1])
		
		return self._parameters[-1]

	def set_objective(self,string,gradientdict=None):
		"""
		sets the objective function
		
		Arguments:
		string:        string representation of the objective using the variable and parameter names
		gradientdict:  optional, dictionary containing key, value pairs with the derivative of the objective with respect to the key. If not supplied the gradient will be calculated symbolically using sympy
		
		Example:
		nlp = parsenlp.Problem()
		nlp.add_variable('x')
		nlp.add_variable('y')
		nlp.set_objective('(x-y)**2',gradientdict = {'x':'2*x-2*y', 'y':'2*y-2*x'})
		"""
		
		self.objective = Function(string,self._variables,self._parameters,gradientdict=gradientdict)

	def add_constraint(self,string,gradientdict=None,lowerbound=None,upperbound=None,name=None):
		"""
		adds a constraint to the optimization problem in the form of:
		lower bound <= constraint value <= upper bound
		when the lower and upper bounds are equal an equality constraint arises
		
		Arguments:
		string:        string representation of the constraint using the variable and parameter names
		gradientdict:  optional, dictionary containing key, value pairs with the derivative of the constraint with respect to the key. If not supplied the gradient will be calculated symbolically using sympy
		lowerbound:    optional, float lower bound of the constraint value
		upperbound:    optional, float upper bound of the constraint value
		name:          optional, string name to reference the constraint
		
		Example:
		nlp = parsenlp.Problem()
		nlp.add_variable('x')
		nlp.add_variable('y')
		nlp.set_objective('x*y',gradientdict={'x':'y', 'y':'x'},lowerbound=10,name='non linear inequality')
		nlp.constraints['non linear inequality'].lowerbound
		nlp.constraints['non linear inequality'].upperbound
		"""
		
		if name == None:
			name = len(self._constraints)
		self._constraints.append( Constraint(string,self._variables,self._parameters,gradientdict=gradientdict,lowerbound=lowerbound,upperbound=upperbound,name=name) )
		self.constraints._add(self._constraints[-1])
		
		return self._constraints[-1]

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
		for c in self._constraints:
			result.append( c(x) )

		return np.array(result,dtype=np.float)

	def jacobian(self,x,flag):
		"""
		computes the constraint jacobian matrix in the sparse form ipopt requires
		
		Arguments:
		x:     list or numpy array of values with length equal to the number of variables
		flag:  boolean, when True the rows and columns of all always non zero entries are returned when False the values of these elements are returned
		"""
		
		if flag:
			row = []
			col = []
			
			for i,c in enumerate(self._constraints):
				for j,g in enumerate(c.gradientexpression):
					if g != '0':
						row.append(i)
						col.append(j)

			return (np.array(row),np.array(col))
		else:
			val = []
			for i,c in enumerate(self._constraints):
				grad = c.gradient(x)
				for j,g in enumerate(c.gradientexpression):
					if g != '0':
						val.append(grad[j])

			return np.array(val,dtype=np.float)


	# get functions
	def get_variable_lowerbounds(self):
		"""
		returns the lower bounds of all variables
		"""
		
		values = []
		for i in self._variables:
			values.append(i.lowerbound)
		
		return np.array(values)

	def get_variable_upperbounds(self):
		"""
		returns the upper bounds of all variables
		"""
		
		values = []
		for i in self._variables:
			values.append(i.upperbound)
		
		return np.array(values)

	def get_constraint_lowerbounds(self):
		"""
		returns the lower bounds of all constraints
		"""
		
		values = []
		for i in self._constraints:
			values.append(i.lowerbound)
		
		return np.array(values)

	def get_constraint_upperbounds(self):
		"""
		returns the upper bounds of all constraints
		"""
		
		values = []
		for i in self._constraints:
			values.append(i.upperbound)
		
		return np.array(values)

	def get_values(self):
		"""
		returns the values of all variables. These are initial values if the problem is not solved yet and the solution after problem.solve() is called
		"""
		
		return np.array([v.value for v in self._variables])

	def set_values(self,x):
		"""
		sets the values of all variables, these will be used as initial values in a subsequent call to problem.solve()
		
		Arguments:
		x:  list or numpy.array with values, with length equal to the number of variables
		"""
		
		for var,val in zip(self._variables,x):
			var.value = val

	# solve the problem using pyipopt
	def solve(self,x0=None):
		"""
		solves the problem using ipopt. The solution is set to variable.value
		
		Arguments:
		x0:  optional, list or numpy.array initial guess. If not supplied the current variable values will be used
		"""
		
		if x0 == None:
			x0 = self.get_values()
		try:
			pyipoptproblem = pyipopt.create(len(self._variables),
											self.get_variable_lowerbounds(),
											self.get_variable_upperbounds(),
											len(self._constraints),
											self.get_constraint_lowerbounds(),
											self.get_constraint_upperbounds(),
											len(self.jacobian(x0,False)),
											0,
											self.objective,
											self.gradient,
											self.constraint,
											self.jacobian)

			x, zl, zu, constraint_multipliers, obj, status = pyipoptproblem.solve(x0)
			self.set_values(x)
			pyipoptproblem.close()
		except:
			raise Exception('pyipopt not found. You can try solving the problem using another solver using the parsenlp.Problem.objective, parsenlp.Problem.gradient, parsenlp.Problem.constraint, parsenlp.Problem.jacobian functions')
		
	
	
###############################################################################
# ObjectContainer                                                             #
###############################################################################
class ObjectContainer:
	"""
	Container class for objects with names to allow easy access
	"""
	def __init__(self):
		self.objects = {}
		
	def _add(self,obj):
		# check if it is an indexed variable
		if isinstance(obj.name, str):
			i = obj.name.find('[')
			if  i>0:
				var = obj.name[:i]
				ind = obj.name[i+1:-1]
			
				# create a dummy np array witch ranges to the maximum dimension
				ind = tuple(int(i) for i in ind.split(','))
				dim = [int(i)+1 for i in ind]
				if var in self.objects:
					for i,(s,d) in enumerate( zip( self.objects[var].shape,dim) ):
						if s > d:
							dim[i] = s
				dim = tuple(dim)
				
				temp = np.empty(dim,dtype=object)
				if var in self.objects:
				
					for i, v in np.ndenumerate(self.objects[var]):
						temp[i] = v
					
				# fill in the current index
				temp[ind] = obj
				self.objects[var] = temp

		# either way add the full obj name to the dictionary so both outer indexing and string indexing is possible
		self.objects[obj.name] = obj
			
	def __getitem__(self,key):
		return self.objects[key]
		
	def keys(self):
		return self.objects.keys()	
		
		
###############################################################################
# Variable                                                                    #
###############################################################################
class Variable:
	def __init__(self,name,symvar,evalvar,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
	
		if name.find('_x_') >=0:
			raise Exception('"_x_" is not allowed in a variable name, {}'.format(name))
			
		if name.find('_p_') >=0:
			raise Exception('"_p_" is not allowed in a variable name, {}'.format(name))
	
		self.name = name
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self._symvar = symvar
		self._evalvar = evalvar
		if value==None:	
			self.value = 0.5*self.lowerbound + 0.5*self.upperbound
		else:
			self.value = value

	def set_lowerbound(self,value):
		self.lowerbound = value
		
	def set_upperbound(self,value):
		self.upperbound = value
		
###############################################################################	
# Function                                                                    #
###############################################################################
class Function:
	def __init__(self,string,variables,parameters,gradientdict=None):
		"""
		defines a function to be used in the optimization problem

		Arguments:
		string:          string to represent the expression
		variables:       list of parsenlp.Variable, optimization problem variables
		parameters:      list of parsenlp.Parameter, optimization problem parameters
		gradientdict:  optional, dictionary of strings which represent the nonzero derivatives with the variable name as key
		"""
		self.variables = variables
		self.parameters = parameters

		
		self.expression = string
		self.sympyexpression = self.name2sympy(self.expression)
		self.evaluationstring = self.name2eval(self.expression)

		# calculate gradient
		if gradientdict==None:
			self.gradientsympyexpression = self.calculate_gradient()
			self.gradientexpression = []

			for g in self.gradientsympyexpression:
				self.gradientexpression.append( self.sympy2name(g) )

		else:
			self.gradientexpression = []
			for v in self.variables:
				if v.name in gradientdict:
					self.gradientexpression.append(gradientdict[v.name])
				else:
					self.gradientexpression.append('0')
			
		# calculate the evaluation string		
		self.gradientevaluationstring = []
		for g in self.gradientexpression:
			self.gradientevaluationstring.append( self.name2eval( g ) )
				
		self.gradientevaluationstring = 'np.array([' + ','.join(self.gradientevaluationstring) + '],dtype=np.float)'
		
	def gradient2dictionary(self):
		"""
		returns a dictionary containing the non zero derivative with the variable name as key 
		"""
		dictionary = {}
		for v,g in zip(self.variables,self.gradientexpression):
			if g != '0':
				dictionary[v.name] = g
		return dictionary
		
	def name2sympy(self,string):
		"""
		replace variable and parameter names with sympy variables
		"""
		
		sympyexpression = string
		for p in self.parameters:
			sympyexpression = sympyexpression.replace(p.name,str(p._symvar))
		for v in self.variables:
			sympyexpression = sympyexpression.replace(v.name,str(v._symvar))
			
		return sympyexpression
	
	def name2eval(self,string):
		"""
		replace variable and parameter names with evaluation variables
		"""
		
		specialfunctions = {'log(':'np.log(','exp(':'np.exp(','sin(':'np.sin(','cos(':'np.cos(','tan(':'np.tan('}

		evaluationstring = string
		for p in self.parameters:
			evaluationstring = evaluationstring.replace(p.name,p._evalvar )
		for v in self.variables:
			evaluationstring = evaluationstring.replace(v.name,v._evalvar)
		
		for f in specialfunctions:
			evaluationstring = evaluationstring.replace(f,specialfunctions[f])
			
		return evaluationstring
	
	def sympy2name(self,sympyexpression):
		"""
		replace sympy variables and parameters with variable names
		"""
		
		expression = sympyexpression
		# reversed so x34 get replaced before x3
		for v in self.variables:
			expression = expression.replace(str(v._symvar),v.name)
		for p in reversed(self.parameters):
				expression = expression.replace(str(p._symvar),p.name)
			
		return expression
		
		
	def calculate_gradient(self):
		"""
		returns a list of strings which contain the derivatives to all variables with sympy names
		"""
		
		gradientsympyexpression = []
		for v in self.variables:
			try:
				gradientsympyexpression.append( str(sympy.diff(self.sympyexpression,v._symvar)) )
			except:
				raise Exception('Error while differentiating constraint: '+self.expression)
		return gradientsympyexpression
		
	
	def __call__(self,_x_):
		"""
		return the function result
		"""
		_p_ = np.array([p.value for p in self.parameters])
		return eval(self.evaluationstring)


	def gradient(self,_x_):
		"""
		return the gradient result
		"""
		_p_ = np.array([p.value for p in self.parameters])
		return eval(self.gradientevaluationstring)

###############################################################################
# Constraint                                                                  #
###############################################################################
class Constraint(Function):
	def __init__(self,string,variables,parameters,gradientdict=None,lowerbound=None,upperbound=None,name=''):
		Function.__init__(self,string,variables,parameters,gradientdict=gradientdict)
		
		if lowerbound == None and upperbound == None:
			lowerbound = 0
			upperbound = 0
		elif lowerbound == None:
			lowerbound = min(0,upperbound)
		elif upperbound == None:
			upperbound = max(0,lowerbound)

		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self.name = name

	def set_lowerbound(self,value):
		self.lowerbound = value

	def set_upperbound(self,value):
		self.upperbound = value

