import parsenlp
import numpy as np


with open('nlp.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')

problem = parsenlp.Problem(jsonstring)

# variables
print('Problem Variables')
print([var.expression for var in problem.variables])

x = problem.get_values()
print(x)
v = problem.get_value_dict()
print(v)

# objective
print('Problem Objective')
print( problem.objective(x) )
print( problem.objective.gradient(x) )

# constraints
print('Single constraint')
print( problem.constraints[0].expression )
print( problem.constraints[0].lowerbound )
print( problem.constraints[0].upperbound )

print( problem.constraints[0](x) )
print( problem.constraints[0].gradient(x) )


# gradient
print('Problem Gradient')
print( problem.gradient(x) )

# constraint
print('Problem Constraints')
print( problem.constraint(x) )
print( problem.get_constraint_upperbounds() )

# jacobian
print('Problem Jacobian')
print( problem.jacobian(x,True) )
print( problem.jacobian(x,False) )