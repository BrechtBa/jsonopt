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



# load the problem from a file in json format
with open('json/hs071.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')

best_known_objective = 17.0140173
	
# parse the problem
problem = parsenlp.Problem(jsonstring)

# set initial guess
x = problem.get_values()
x[:4] = np.array([1.,5.,5.,1.])

# solve and get the solution
problem.solve(x0=x)
sol = problem.get_value_dict()
obj = problem.objective(problem.get_values()) 

print( 'solution: {}'.format(sol['x']) )
print( 'objective: {}'.format(obj) )


if abs( (obj - best_known_objective)/best_known_objective ) < 0.001:
	print( 'OK' )
else:
	print( 'NOK, best known objective: {}, current objective: {}'.format(best_known_objective,obj) )
