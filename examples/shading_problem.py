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

# shading problem:
#
# This is an optimization problem I have been working on just as a test
# The goal of the optimization is to control the shades of a building in a desirable way
# The shades are used to track a setpoint of solar irradiation through the building windows
# The setpoint and maximum irradiation can vary over time and needs to be tracked within a certain boundary
# The second objective is maximizing the view through the windows
# To limit the number of movements a move cost is added which rises quickly to one is any of the shades move.
# As it is a multi objective problem a trade-off will be made between setpoint tracking, view maximization and movement minimization

import numpy as np
import parsenlp

N = 8  # time steps
M = 4  # windows

problem = parsenlp.Problem()

p0 = 0.60*np.ones(M)
Qset = 1000.*np.ones(N)

Qopen = np.vstack((np.linspace(1000.,0.,N),np.linspace(600.,0.,N),np.linspace(800.,0.,N),np.linspace(400.,0.,N))).transpose()
Qclosed = 0.2*Qopen


# add variables
print('adding variables')
p = np.empty((N,M), dtype=object)
move = np.empty((N), dtype=object)
Q = np.empty((N), dtype=object)
Qslack_min = np.empty((N), dtype=object)
Qslack_max = np.empty((N), dtype=object)
for i in range(N):
	for j in range(M):

		p[i,j] = problem.add_variable(parsenlp.Expression('p[i,j]',['i','j'],[[i],[j]]).parse(),lowerbound=0.0,upperbound=1.0)

	move[i] = problem.add_variable(parsenlp.Expression('move[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=1.0)
	Q[i] = problem.add_variable(parsenlp.Expression('Q[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=sum(Qopen[i,:]))
	Qslack_min[i] = problem.add_variable(parsenlp.Expression('Qslack_min[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=20.e3)
	Qslack_max[i] = problem.add_variable(parsenlp.Expression('Qslack_max[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=20.e3)


# add parameters
print('adding parameters')
dQ = problem.add_parameter('dQ',100)
c_move = problem.add_parameter('c_move',200.)
c_view = problem.add_parameter('c_view',100./N/M)
for j in range(M):
	problem.add_parameter(parsenlp.Expression('p0[j]',['j'],[[j]]).parse(),p0[j])

for i in range(N):

	problem.add_parameter(parsenlp.Expression('Qset[i]',['i'],[[i]]).parse(),Qset[i])
	
	for j in range(M):

		problem.add_parameter(parsenlp.Expression('Qopen[i,j]',['i','j'],[[i],[j]]).parse(),Qopen[i,j])
		problem.add_parameter(parsenlp.Expression('Qclosed[i,j]',['i','j'],[[i],[j]]).parse(),Qclosed[i,j])	



# set objective
print('setting objective')
problem.set_objective(parsenlp.Expression('sum(Qslack_min[i],i) + sum(Qslack_max[i],i) + c_move*sum(move[i],i) + sum(sum(c_view*p[i,j],i),j)',['i','j'],[range(N),range(M)]).parse()) 


# add constraints
print('adding constraints')
for i in range(N):
	problem.add_constraint(parsenlp.Expression('Q[i]-sum((1-p[i,j])*Qopen[i,j]+p[i,j]*Qclosed[i,j],j)',['i','j'],[[i],range(M)]).parse(),lowerbound=0.,upperbound=0.)
	problem.add_constraint(parsenlp.Expression('Qslack_min[i]-Qset[i]+dQ+Q[i]',['i'],[[i]]).parse(),lowerbound=0.,upperbound=20.e2)
	problem.add_constraint(parsenlp.Expression('Qslack_max[i]+Qset[i]+dQ-Q[i]',['i'],[[i]]).parse(),lowerbound=0.,upperbound=20.e3 )

	for j in range(M):
		if i==0:
			problem.add_constraint(parsenlp.Expression('move[i]-(1-exp(-200*(p[i,j]-p0[j])**2))',['i','j'],[[i],[j]]).parse(),lowerbound=0.,upperbound=10.)
		else:
			# custom gradient definition
			gradientdict = {}
			gradientdict[parsenlp.Expression('move[i]',['i'],[[i]]).parse()] = '1'
			gradientdict[parsenlp.Expression('p[i,j]',['i','j'],[[i],[j]]).parse()]   = parsenlp.Expression('(-400*p[i,j] + 400*p[i-1,j])*exp(-200*(p[i,j] - p[i-1,j])**2)',['i','j'],[[i],[j]]).parse()
			gradientdict[parsenlp.Expression('p[i-1,j]',['i','j'],[[i],[j]]).parse()] = parsenlp.Expression('( 400*p[i,j] - 400*p[i-1,j])*exp(-200*(p[i,j] - p[i-1,j])**2)',['i','j'],[[i],[j]]).parse()
			problem.add_constraint(parsenlp.Expression('move[i]-(1-exp(-200*(p[i,j]-p[i-1,j])**2))',['i','j'],[[i],[j]]).parse(),gradientdict=gradientdict,lowerbound=0.,upperbound=10.)

print('solving')
problem.solve()
x = problem.get_values()

print(' ')
for j in range(M):
	print( ['{:.2f}'.format(p[i,j].value) for i in range(N)] )

print(' ')
print('move')
print( ['{:.2f}'.format(move[i].value) for i in range(N)] )

print(' ')
print('Q')
print( ['{:.0f}'.format(Q[i].value) for i in range(N)] )

print(' ')
print('Qslack_min')
print( ['{:.0f}'.format(Qslack_min[i].value) for i in range(N)] )

print(' ')
print('Qslack_max')
print( ['{:.0f}'.format(Qslack_max[i].value) for i in range(N)] )



