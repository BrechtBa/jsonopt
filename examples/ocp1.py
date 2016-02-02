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
with open('json/ocp1.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')

	
# parse the problem
problem = parsenlp.Problem(jsonstring)

# solve and get the solution
problem.solve()
sol = problem.get_value_dict()

# plot
t = np.arange(sol['p'].shape[0])

print(sol['T'])
print(sol['Q'])
print(sol['P'])

