import parseipopt



with open('nlp.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')
#jsonstring = r'{"variables":["T[i] for i in range(25)","P[i] for i in range(24)","Q[i] for i in range(24)","COP[i] for i in range(24)"]}'

problem = parseipopt.Problem(jsonstring)


print(problem.variables[0].expression)
print(problem.variables[0].lowerbound)
print(problem.variables[0].upperbound)
print(problem.variables[-1].expression)
print(problem.variables[-1].lowerbound)
print(problem.variables[-1].upperbound)