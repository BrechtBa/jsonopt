import parsepyipopt


expression = parsepyipopt.Expression('sum(sum(p[i,j],i),j)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print( sumexpression[0] )
print( argument[0].expression )
print( index[0] )

sumexpression,argument,index = argument[0].find_sum()
print( sumexpression[0] )
print( argument[0].expression )
print( index[0] )


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
