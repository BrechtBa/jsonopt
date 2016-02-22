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


import parsenlp
import numpy as np


with open('json/ocp1.json', 'r') as jsonfile:
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

# # constraints
print('Single constraint')
print( problem.constraints[0].expression )
print( problem.constraints[0].lowerbound )
print( problem.constraints[0].upperbound )

print( problem.constraints[0](x) )
print( problem.constraints[0].gradient(x) )


# # gradient
print('Problem Gradient')
print( problem.gradient(x) )

# # constraint
print('Problem Constraints')
print( problem.constraint(x) )
print( problem.get_constraint_upperbounds() )

# # jacobian
print('Problem Jacobian')
print( problem.jacobian(x,False) )
print( problem.jacobian(x,True) )
