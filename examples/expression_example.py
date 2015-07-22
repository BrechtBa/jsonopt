import parsepyipopt

print(' ')
print('find single of sums:')
expression = parsepyipopt.Expression('A + sum(p[i,0],i)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print(expression.string)
print( [e.string for e in sumexpression] )
print( [a.string for a in argument] )
print( index )


print(' ')
print('find series of sums:')
expression = parsepyipopt.Expression('A + sum(p[i,0],i) + sum(p[0,j],j)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print(expression.string)
print( [e.string for e in sumexpression] )
print( [a.string for a in argument] )
print( index )


print(' ')
print('find nested sum:')
expression = parsepyipopt.Expression('sum(sum(p[i,j],i),j)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print(expression.string)
print( sumexpression[0].string )
print( argument[0].string )
print( index[0] )

sumexpression,argument,index = argument[0].find_sum()
print( sumexpression[0].string )
print( argument[0].string )
print( index[0] )

print(' ')
print('find sums in expression without sum:')
expression = parsepyipopt.Expression('p[i,j]',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print( sumexpression )
print( argument )
print( index )


print(' ')
print('parse simple:')
expression = parsepyipopt.Expression('p[i,j] + 5*q[i] + 10*r[j,i]',['i','j'],[[0],[1]])
print(expression.string)
print(expression.parse())

print(' ')
print('parse simple sum:')
expression = parsepyipopt.Expression('p[i,j] + 5*q[i] + 10*sum(r[j,a],a)',['i','j','a'],[[0],[1],[0,1,2]])
print(expression.string)
print(expression.parse())

print(' ')
print('parse nested sum:')
expression = parsepyipopt.Expression('p[i,j] + 5*q[i] + 10*sum(sum(sum(s[c]*r[a,b],a),b),c)',['i','j','a','b','c'],[[0],[1],[0,1,2,3],[0,1,2],[0,1]])
print(expression.string)
print(expression.parse())



#print( [e.expression for e in expression.parse_braces()] )

#expression = parsepyipopt.Expression('Q[i]-sum((1-p[i,j])*Qopen[i,j]+p[i,j]*Qclosed[i,j],j)',['i','j'],[[0],[0,1,2]])
#print( expression.expression )
#print( expression.parse() )
#print(' ')


#expression = parsepyipopt.Expression('sum(sum(p[i,j],j),i)',['i','j'],[[0,1],[0,1,2]])
#print( expression.expression )
#print( expression.parse() )
#print(' ')




#expression = parsepyipopt.Expression('(A+(B))+(C)',['i','j'],[[0],[0,1,2]])
#print( [e.expression for e in expression.parse_braces()] )
