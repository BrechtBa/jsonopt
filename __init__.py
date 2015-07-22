

import numpy as np
import sympy
#import pyipopt
import re

class Problem:
	def __init__(self):
		self.variables = []
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
		symvar = sympy.Symbol( 'symvar{0}'.format(len(self.variables)) )
		evalvar = 'symvar[{0}]'.format(len(self.variables))
		self.variables.append( Variable(name,symvar,evalvar,lowerbound=value,upperbound=value) )
		return self.variables[-1]

	def set_objective(self,expressionstring):
		self.objective = Function(expressionstring,self.variables)

	def add_constraint(self,expressionstring,lowerbound=0.0,upperbound=0.0,name=''):
		self.constraints.append( Constraint(expressionstring,self.variables,lowerbound,upperbound,name) )
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
			i.sol = s

		nlp.close()

	def get_solution(self):
		return np.array([v.sol for v in self.variables])


# Variables
class Variable:
	def __init__(self,name,symvar,evalvar,lowerbound=-1.0e20,upperbound=1.0e20):
		self.name = name
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self._symvar = symvar
		self._evalvar = evalvar
		self.sol = None
 
	def set_lowerbound(self,value):
		self.lowerbound = value

	def set_upperbound(self,value):
		self.upperbound = value


# Functions
class Function:
	def __init__(self,expression,variables):

		self.variables = variables

		self.expression = expression
		self.parsedexpression = self.expression.parse()
		self.sympyexpression = self.parsedexpression
		self.evaluationstring = self.parsedexpression

		self.gradientexpression = []
		self.gradientsympyexpression = []
		self.gradientevaluationstring = ''

		specialfunctions = {'log(':'np.log(','exp(':'np.exp('}

		# parse the function
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

			self.gradientexpression.append( temp_gradientexpression )
			gradientevaluationstring.append( temp_gradientevaluationstring )

		self.gradientevaluationstring = 'np.array([' + ','.join(gradientevaluationstring) + '],dtype=np.float)'

		# replace special functions with their numpy equivalent
		for f in specialfunctions:
			self.evaluationstring = self.evaluationstring.replace(f,specialfunctions[f])
			self.gradientevaluationstring = self.gradientevaluationstring.replace(f,specialfunctions[f])
			
	def __call__(self,symvar):
		return eval(self.evaluationstring)


	def gradient(self,symvar):
		return eval(self.gradientevaluationstring)


# Constraint
class Constraint(Function):
	def __init__(self,expression,variables,lowerbound=0.0,upperbound=0.0,name=''):
		Function.__init__(self,expression,variables)
		self.lowerbound = lowerbound
		self.upperbound = upperbound
		self.name = name

	def set_lowerbound(self,value):
		self.lowerbound = value

	def set_upperbound(self,value):
		self.upperbound = value





class Expression:
	"""
	A class to parse mathematical expressions containing indexes and sums as commonly encountered in optimization problem definitions
	"""
	def __init__(self,string,indexnames,indexvalues):
		self.string = string
		self.indexnames = indexnames
		self.indexvalues = indexvalues
		
	def parse(self):
		"""
		expand the expression
		"""
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

	def replace_index(self,expression,index,value):
		pre = ['[',',']
		delta = [-3,-2,-1,+1,+2,+3]

		for p in pre:
			for d in delta:
				expression = re.sub(re.escape(p)+index+'{:+.0f}'.format(d),p+'{:.0f}'.format(value),expression)

			expression = re.sub(re.escape(p)+index,p+'{:.0f}'.format(value),expression)

		return expression


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