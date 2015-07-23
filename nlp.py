#!/usr/bin/python3


#	This file is part of parsepyipopt.
#
#    parsepyipopt is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    parsepyipopt is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with parsepyipopt.  If not, see <http://www.gnu.org/licenses/>.


import numpy as np
import sympy
import pyipopt


class Problem:
	def __init__(self):
		self.variables = []
		self.parameters = []
		self.objective = None
		self.constraints = []

	def add_variable(self,name,lowerbound=-1.0e20,upperbound=1.0e20):
		symvar = sympy.Symbol( 'symvar{0}'.format(len(self.variables)) )
		evalvar = 'symvar[{0}]'.format(len(self.variables))
		self.variables.append( Variable(name,symvar,evalvar,lowerbound=lowerbound,upperbound=upperbound) )
		return self.variables[-1]

	def get_variable(self,name):
		ind = [i.name for i in self.variables].index(name)
		return self.variables[ind]

	def add_parameter(self,name,value):
		symvar = sympy.Symbol( 'sympar{0}'.format(len(self.parameters)) )
		evalvar = 'sympar[{0}]'.format(len(self.parameters))
		self.parameters.append( Variable(name,symvar,evalvar,lowerbound=value,upperbound=value,value=value) )
		return self.parameters[-1]

	def set_objective(self,expressionstring):
		self.objective = Function(expressionstring,self.variables,self.parameters)

	def add_constraint(self,expressionstring,lowerbound=0.0,upperbound=0.0,name=''):
		self.constraints.append( Constraint(expressionstring,self.variables,self.parameters,lowerbound,upperbound,name) )
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
		for i in self.variables:
			values.append(i.lowerbound)
		
		return np.array(values)

	def get_variable_upperbounds(self):
		values = []
		for i in self.variables:
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


	# problem solution
	def solve(self,x0):

		nlp = pyipopt.create(len(self.variables), self.get_variable_lowerbounds(), self.get_variable_upperbounds(), len(self.constraints), self.get_constraint_lowerbounds(), self.get_constraint_upperbounds(), len(self.jacobian(x0,False)), 0, self.objective, self.gradient, self.constraint, self.jacobian)
		x, zl, zu, constraint_multipliers, obj, status = nlp.solve(x0)

		for i,s in zip(self.variables,x):
			i.value = s

		nlp.close()

	def get_solution(self):
		return np.array([v.value for v in self.variables])


# Variables
class Variable:
	def __init__(self,name,symvar,evalvar,lowerbound=-1.0e20,upperbound=1.0e20,value=None):
		self.name = name
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self._symvar = symvar
		self._evalvar = evalvar
		self.value = value
 
	def set_lowerbound(self,value):
		self.lowerbound = value
		
	def set_upperbound(self,value):
		self.upperbound = value

# Functions
class Function:
	def __init__(self,expression,variables,parameters):

		self.variables = variables
		self.parameters = parameters

		self.expression = expression
		self.parsedexpression = self.expression.parse()
		self.sympyexpression = self.parsedexpression
		self.evaluationstring = self.parsedexpression

		self.gradientexpression = []
		self.gradientsympyexpression = []
		self.gradientevaluationstring = ''

		specialfunctions = {'log(':'np.log(','exp(':'np.exp('}

		# parse the function
		for p in self.parameters:
			self.sympyexpression = self.sympyexpression.replace(p.name,str(p._symvar))
			self.evaluationstring = self.evaluationstring.replace(p.name,p._evalvar )
		
		for v in self.variables:
			self.sympyexpression = self.sympyexpression.replace(v.name,str(v._symvar))
			self.evaluationstring = self.evaluationstring.replace(v.name,v._evalvar )
		
		
		# create gradients
		gradientevaluationstring = []
		for v in self.variables:
			try:
				self.gradientsympyexpression.append( str(sympy.diff(self.sympyexpression,v._symvar)) )
			except:
				raise Exception('Error while diferentiating constraint: '+self.parsedexpression)

		for g in self.gradientsympyexpression:
			temp_gradientexpression = g
			temp_gradientevaluationstring = g
			for v in reversed(self.variables):
				# reversed so x34 get replaced before x3
				temp_gradientexpression = temp_gradientexpression.replace(str(v._symvar),v.name)
				temp_gradientevaluationstring = temp_gradientevaluationstring.replace(str(v._symvar),v._evalvar)

			for p in reversed(self.parameters):
				temp_gradientexpression = temp_gradientexpression.replace(str(p._symvar),p.name)
				temp_gradientevaluationstring = temp_gradientevaluationstring.replace(str(p._symvar),p._evalvar)
				
			self.gradientexpression.append( temp_gradientexpression )
			gradientevaluationstring.append( temp_gradientevaluationstring )

		self.gradientevaluationstring = 'np.array([' + ','.join(gradientevaluationstring) + '],dtype=np.float)'

		# replace special functions with their numpy equivalent
		for f in specialfunctions:
			self.evaluationstring = self.evaluationstring.replace(f,specialfunctions[f])
			self.gradientevaluationstring = self.gradientevaluationstring.replace(f,specialfunctions[f])
			
	def __call__(self,symvar):
		sympar = np.array([p.value for p in self.parameters])
		return eval(self.evaluationstring)


	def gradient(self,symvar):
		sympar = np.array([p.value for p in self.parameters])
		return eval(self.gradientevaluationstring)


# Constraint
class Constraint(Function):
	def __init__(self,expression,variables,parameters,lowerbound=0.0,upperbound=0.0,name=''):
		Function.__init__(self,expression,variables,parameters)
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self.name = name

	def set_lowerbound(self,value):
		self.lowerbound = value

	def set_upperbound(self,value):
		self.upperbound = value

