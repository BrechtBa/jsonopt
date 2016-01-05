import parseipopt
import numpy as np


with open('nlp.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')

problem = parseipopt.Problem(jsonstring)

# variables
print('')
print([var.expression for var in problem.variables])
print(problem.variables[1].index)

x = problem.get_temp_values();

# objective
print('')
print( problem.objective(x) )
print( problem.objective.gradient(x) )

# constraints
print('')
print(problem.constraints[0].expression)
print(problem.constraints[0].lowerbound)
print(problem.constraints[0].upperbound)

print(problem.constraints[0](x) )
print(problem.constraints[0].gradient(x) )
