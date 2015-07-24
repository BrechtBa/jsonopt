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

print(' ')
print('find single of sums:')
expression = parsenlp.Expression('A + sum(p[i,0],i)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print(expression.string)
print( [e.string for e in sumexpression] )
print( [a.string for a in argument] )
print( index )


print(' ')
print('find series of sums:')
expression = parsenlp.Expression('A + sum(p[i,0],i) + sum(p[0,j],j)',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print(expression.string)
print( [e.string for e in sumexpression] )
print( [a.string for a in argument] )
print( index )


print(' ')
print('find nested sum:')
expression = parsenlp.Expression('sum(sum(p[i,j],i),j)',['i','j'],[[0,1],[0,1,2]])
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
expression = parsenlp.Expression('p[i,j]',['i','j'],[[0,1],[0,1,2]])
sumexpression,argument,index = expression.find_sum()
print( sumexpression )
print( argument )
print( index )


print(' ')
print('parse simple:')
expression = parsenlp.Expression('p[i+3,j] + 5*q[i] + 10*r[j-1,i]',['i','j'],[[0],[1]])
print(expression.string)
print(expression.parse())

print(' ')
print('parse simple sum:')
expression = parsenlp.Expression('p[i,j] + 5*q[i] + 10*sum(r[j,a],a)',['i','j','a'])
print(expression.string)
print(expression.parse([[0],[1],[0,1,2]]))

print(' ')
print('parse nested sum:')
expression = parsenlp.Expression('p[i,j] + 5*q[i] + 10*sum(sum(sum(s[c]*r[a,b],a),b),c)',['i','j','a','b','c'],[[0],[1],[0,1,2,3],[0,1,2],[0,1]])
print(expression.string)
print(expression.parse())
