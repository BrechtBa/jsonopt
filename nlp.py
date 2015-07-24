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


import numpy as np
import sympy
#import pyipopt


class Problem:
	def __init__(self):
		self.variables = Variables()
		self._variables = []
		self.parameters = Variables()
		self._parameters = []
		self.objective = None
		self.constraints = []
		
	def add_variable(self,name,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
		
		if value==None:
			value = 0.5*lowerbound + 0.5*upperbound

		symvar = sympy.Symbol( 'symvar{0}'.format(len(self._variables)) )
		evalvar = 'symvar[{0}]'.format(len(self._variables))
		self._variables.append( Variable(name,symvar,evalvar,lowerbound=lowerbound,upperbound=upperbound,value=value) )
		self.variables._add(self._variables[-1])
		
		return self._variables[-1]

	def get_variable(self,name):
		ind = [i.name for i in self._variables].index(name)
		return self._variables[ind]

	def add_parameter(self,name,value):
		symvar = sympy.Symbol( 'sympar{0}'.format(len(self._parameters)) )
		evalvar = 'sympar[{0}]'.format(len(self._parameters))
		self._parameters.append( Variable(name,symvar,evalvar,lowerbound=value,upperbound=value,value=value) )
		self.parameters._add(self._parameters[-1])
		
		return self._parameters[-1]

	def set_objective(self,string,gradientdict=None):
		self.objective = Function(string,self._variables,self._parameters,gradientdict=gradientdict)

	def add_constraint(self,string,gradientdict=None,lowerbound=0.0,upperbound=0.0,name=''):
		self.constraints.append( Constraint(string,self._variables,self._parameters,gradientdict=gradientdict,lowerbound=lowerbound,upperbound=upperbound,name=name) )
		return self.constraints[-1]

	def get_constraint(self,name):
		ind = [i.name for i in self.constraints].index(name)
		return self.constraints[ind]

	# callbacks
	def gradient(self,symvar):
		return self.objective.gradient(symvar);

	def constraint(self,symvar):
		result = []
		for c in self.constraints:
			result.append( c(symvar) )

		return np.array(result,dtype=np.float)

	def jacobian(self,symvar,flag):
		if flag:
			row = []
			col = []
			
			for i,c in enumerate(self.constraints):
				for j,g in enumerate(c.gradientexpression):
					if g != '0':

						row.append(i)
						col.append(j)

			return (np.array(row),np.array(col))
		else:
			val = []
			for i,c in enumerate(self.constraints):

				grad = c.gradient(symvar)
				for j,g in enumerate(c.gradientexpression):
					if g != '0':
						val.append(grad[j])

			return np.array(val,dtype=np.float)


	# get functions
	def get_variable_lowerbounds(self):
		values = []
		for i in self._variables:
			values.append(i.lowerbound)
		
		return np.array(values)

	def get_variable_upperbounds(self):
		values = []
		for i in self._variables:
			values.append(i.upperbound)
		
		return np.array(values)

	def get_constraint_lowerbounds(self):
		values = []
		for i in self.constraints:
			values.append(i.lowerbound)
		
		return np.array(values)

	def get_constraint_upperbounds(self):
		values = []
		for i in self.constraints:
			values.append(i.upperbound)
		
		return np.array(values)

	def get_values(self):
		return np.array([v.value for v in self._variables])

	def set_values(self,x):
		for var,val in zip(self._variables,x):
			var.value = val


	# solve the problem using pyipopt
	def solve(self,x0=None):
		
		if x0 == None:
			x0 = self.get_values()
		
		nlp = pyipopt.create(   len(self._variables),
								self.get_variable_lowerbounds(),
								self.get_variable_upperbounds(),
								len(self.constraints),
								self.get_constraint_lowerbounds(),
								self.get_constraint_upperbounds(),
								len(self.jacobian(x0,False)),
								0,
								self.objective,
								self.gradient,
								self.constraint,
								self.jacobian)

		x, zl, zu, constraint_multipliers, obj, status = nlp.solve(x0)
		self.set_values(x)
		nlp.close()

###############################################################################
# Variable                                                                    #
###############################################################################
class Variable:
	def __init__(self,name,symvar,evalvar,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
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
# Variables                                                                   #
###############################################################################
class Variables:
	"""
	Container class for variables to allow easy access
	"""
	def __init__(self):
		self.variables = {}
		
	def _add(self,variable):
		# check if it is an indexed variable
		var = variable.name
		i = variable.name.find('[')
		if  i>0:
			var = variable.name[:i]
			ind = variable.name[i+1:-1]
		
			# create a dummy np array witch ranges to the maximum dimension
			ind = tuple(int(i) for i in ind.split(','))
			dim = [int(i)+1 for i in ind]
			if var in self.variables:
				for i,(s,d) in enumerate( zip( self.variables[var].shape,dim) ):
					if s > d:
						dim[i] = s
			dim = tuple(dim)
			
			temp = np.empty(dim,dtype=object)
			if var in self.variables:
			
				for i, v in np.ndenumerate(self.variables[var]):
					temp[i] = v
				
			# fill in the current index
			temp[ind] = variable
			self.variables[var] = temp

		# either way add the full variable name to the dictionary so both outer indexing and string indexing is possible
		self.variables[variable.name] = variable
			
	def __getitem__(self,key):
		return self.variables[key]
		
	def keys(self):
		return self.variables.keys()
		
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
		for v in reversed(self.variables):
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
		
	
	def __call__(self,symvar):
		"""
		return the function result
		"""
		sympar = np.array([p.value for p in self.parameters])
		return eval(self.evaluationstring)


	def gradient(self,symvar):
		"""
		return the gradient result
		"""
		sympar = np.array([p.value for p in self.parameters])
		return eval(self.gradientevaluationstring)

###############################################################################
# Constraint                                                                  #
###############################################################################
class Constraint(Function):
	def __init__(self,string,variables,parameters,gradientdict=None,lowerbound=0.0,upperbound=0.0,name=''):
		Function.__init__(self,string,variables,parameters,gradientdict=gradientdict)
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self.name = name

	def set_lowerbound(self,value):
		self.lowerbound = value

	def set_upperbound(self,value):
		self.upperbound = value

