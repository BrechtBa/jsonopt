import numpy as np
import parsepyipopt

index = parsepyipopt.indexedexpression

N = 10  # timesteps
M = 3  # windows

problem = parsepyipopt.problem()

p0 = 0.80*np.ones(M)
Qset = 1000.*np.ones(N)
dQ = 100.

Qopen = np.vstack((np.linspace(1000.,0.,N),np.linspace(600.,0.,N),np.linspace(800.,0.,N))).transpose()
Qclosed = 0.2*Qopen


# add variables
for i in range(N):
	for j in range(M):

		p = problem.add_variable(index('p[i,j]',['i','j'],[i,j]))
		p.set_lowerbound(0.)
		p.set_upperbound(1.)

	move = problem.add_variable(index('move[i]',['i'],[i]))
	Q = problem.add_variable(index('Q[i]',['i'],[i]))
	Qslack_min = problem.add_variable(index('Qslack_min[i]',['i'],[i]))
	Qslack_max = problem.add_variable(index('Qslack_max[i]',['i'],[i]))

	move.set_lowerbound(0.)
	move.set_upperbound(1.)
	Q.set_lowerbound(0.)
	Q.set_upperbound(sum(Qopen[i,:]))
	Qslack_min.set_lowerbound(0.)
	Qslack_min.set_upperbound(20.e3)
	Qslack_max.set_lowerbound(0.)
	Qslack_max.set_upperbound(20.e3)


# add parameters
problem.add_parameter('dQ',dQ)
problem.add_parameter('c_move',5000.)
for j in range(M):
	problem.add_parameter(index('p0[j]',['j'],[j]),p0[j])

for i in range(N):

	problem.add_parameter(index('Qset[i]',['i'],[i]),Qset[i])
	
	for j in range(M):

		problem.add_parameter(index('Qopen[i,j]',['i','j'],[i,j]),Qopen[i,j])
		problem.add_parameter(index('Qclosed[i,j]',['i','j'],[i,j]),Qclosed[i,j])	


# add constraints
for i in range(N):
	problem.add_constraint(index('Q[i]-('+ '+'.join(['(1-p[i,{0}])*Qopen[i,{0}]+p[i,{0}]*Qclosed[i,{0}]'.format(j) for j in range(M)])+')',['i'],[i]),0.,0.)
	problem.add_constraint(index('Qslack_min[i]-Qset[i]+dQ+Q[i]',['i'],[i]),0.,20.e2)
	problem.add_constraint(index('Qslack_max[i]+Qset[i]+dQ-Q[i]',['i'],[i]),0.,20.e3)

	for j in range(M):
		if i==0:
			problem.add_constraint(index('move[i]-(p[i,j]-p0[j])**2',['i','j'],[i,j]),0.,1.)
		else:
			problem.add_constraint(index('move[i]-(p[i,j]-p[i-1,j])**2',['i','j'],[i,j]),0.,1.)

# set objective
problem.set_objective('+'.join([ index('Qslack_min[i]',['i'],[i]) for i in range(N)]) +'+'+ '+'.join([ index('Qslack_max[i]',['i'],[i]) for i in range(N)]) +'+'+ '+'.join([ index('c_move*move[i]',['i'],[i]) for i in range(N)])  )



x0 = problem.get_variable_lowerbounds()
print(x0)
print( problem.objective(x0) )
print( problem.gradient(x0) )
print( problem.constraint(x0) )
print( problem.jacobian(x0,True) )
print( problem.jacobian(x0,False) )


problem.solve(x0)

print(' ')
for i in range(N):
	print( problem.get_variable(index('p[i,0]',['i'],[i])).sol )

print(' ')
for i in range(N):
	print( problem.get_variable(index('p[i,1]',['i'],[i])).sol )

print(' ')
print('Q')
for i in range(N):
	print( problem.get_variable(index('Q[i]',['i'],[i])).sol )

print(' ')
print('Qslack_min')
for i in range(N):
	print( problem.get_variable(index('Qslack_min[i]',['i'],[i])).sol )

print(' ')
print('Qslack_max')
for i in range(N):
	print( problem.get_variable(index('Qslack_max[i]',['i'],[i])).sol )

