import parseipopt
import numpy as np


with open('nlp.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')

problem = parseipopt.Problem(jsonstring)

# # variables
print([var.expression for var in problem.variables])
# print(problem.variables[0].expression)
# print(problem.variables[0].lowerbound)
# print(problem.variables[0].upperbound)
# print(problem.variables[-1].expression)
# print(problem.variables[-1].lowerbound)
# print(problem.variables[-1].upperbound)


# # constraints
# print(problem.constraints[-1].expression)
# print(problem.constraints[-1].lowerbound)
# print(problem.constraints[-1].upperbound)

# print( problem.constraints[-1](problem.variables,[ np.random.random() for var in problem.variables]) )
# print( problem.constraints[-1].gradient(problem.variables,[ np.random.random() for var in problem.variables]) )

# objective
#print( problem.objective(problem.variables,[ np.random.random() for var in problem.variables]) )
#print( problem.objective.gradient(problem.variables,[ np.random.random() for var in problem.variables]) )
