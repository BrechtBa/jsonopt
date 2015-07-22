import numpy as np
import parsepyipopt as pp


N = 10  # timesteps
M = 3  # windows

problem = pp.problem()

p0 = 0.80*np.ones(M)
Qset = 1000.*np.ones(N)
dQ = 100.

Qopen = np.vstack((np.linspace(1000.,0.,N),np.linspace(600.,0.,N),np.linspace(800.,0.,N))).transpose()
Qclosed = 0.2*Qopen


# add variables
p = np.empty((N,M), dtype=object)
move = np.empty((N), dtype=object)
Q = np.empty((N), dtype=object)
Qslack_min = np.empty((N), dtype=object)
Qslack_max = np.empty((N), dtype=object)
for i in range(N):
	for j in range(M):

		p[i,j] = problem.add_variable(pp.Expression('p[i,j]',['i','j'],[[i],[j]]).parse(),lowerbound=0.0,upperbound=1.0)

	move[i] = problem.add_variable(pp.Expression('move[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=1.0)
	Q[i] = problem.add_variable(pp.Expression('Q[i]',['i'],[[i]]),lowerbound=0.0,upperbound=sum(Qopen[i,:]))
	Qslack_min[i] = problem.add_variable(pp.Expression('Qslack_min[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=20.e3)
	Qslack_max[i] = problem.add_variable(pp.Expression('Qslack_max[i]',['i'],[[i]]).parse(),lowerbound=0.0,upperbound=20.e3)

# add parameters
problem.add_parameter('dQ',dQ)
problem.add_parameter('c_move',5000.)
for j in range(M):
	problem.add_parameter(pp.Expression('p0[j]',['j'],[[j]].parse()),p0[j])

for i in range(N):

	problem.add_parameter(pp.Expression('Qset[i]',['i'],[[i]].parse()),Qset[i])
	
	for j in range(M):

		problem.add_parameter(pp.Expression('Qopen[i,j]',['i','j'],[[i],[j]]).parse(),Qopen[i,j])
		problem.add_parameter(pp.Expression('Qclosed[i,j]',['i','j'],[[i],[j]]).parse(),Qclosed[i,j])	


# add constraints
for i in range(N):
	problem.add_constraint(pp.Expression('Q[i]-sum((1-p[i,j])*Qopen[i,j]+p[i,j]*Qclosed[i,j],j)',['i','j'],[[i],range(M)]),0.,0.)
	problem.add_constraint(pp.Expression('Qslack_min[i]-Qset[i]+dQ+Q[i]',['i'],[[i]]),0.,20.e2)
	problem.add_constraint(pp.Expression('Qslack_max[i]+Qset[i]+dQ-Q[i]',['i'],[[i]]),0.,20.e3)

	for j in range(M):
		if i==0:
			problem.add_constraint(pp.Expression('move[i]-(1-exp(-100*(p[i,j]-p0[j])**2))',['i','j'],[[i],[j]]),0.,1.)
		else:
			problem.add_constraint(pp.Expression('move[i]-(1-exp(-100*(p[i,j]-p[i-1,j])**2))',['i','j'],[[i],[j]]),0.,1.)

# set objective
problem.set_objective(pp.Expression('sum(Qslack_min[i],i) + sum(Qslack_max[i],i) + c_move*sum(move[i],i)',['i'],[range(N)])) 


x0 = problem.get_variable_lowerbounds()
print(x0)
print( problem.objective(x0) )
print( problem.gradient(x0) )
print( problem.constraint(x0) )
print( problem.jacobian(x0,True) )
print( problem.jacobian(x0,False) )

problem.solve(x0)


print(' ')
for j in range(M):
	print( ['{:.2f}'.format(p[i,j].sol) for i in range(N)] )

print(' ')
print('Q')
print( ['{:.0f}'.format(Q[i].sol) for i in range(N)] )

print(' ')
print('Q')
print( ['{:.0f}'.format(Qslack_min[i].sol) for i in range(N)] )

print(' ')
print('Q')
print( ['{:.0f}'.format(Qslack_max[i].sol) for i in range(N)] )