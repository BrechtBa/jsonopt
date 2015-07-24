import numpy as np
import parsenlp


N = 8  # timesteps
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
	problem.add_constraint(parsenlp.Expression('Qslack_max[i]+Qset[i]+dQ-Q[i]',['i'],[[i]]).parse(),lowerbound=0.,upperbound=20.e3)

	for j in range(M):
		if i==0:
			problem.add_constraint(parsenlp.Expression('move[i]-(1-exp(-200*(p[i,j]-p0[j])**2))',['i','j'],[[i],[j]]).parse(),lowerbound=0.,upperbound=10.)
		else:
			problem.add_constraint(parsenlp.Expression('move[i]-(1-exp(-200*(p[i,j]-p[i-1,j])**2))',['i','j'],[[i],[j]]).parse(),lowerbound=0.,upperbound=10.)


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
