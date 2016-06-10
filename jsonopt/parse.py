#!/usr/bin/env/ python
################################################################################
#    Copyright 2016 Brecht Baeten
#    This file is part of jsonopt.
#
#    jsonopt is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    jsonopt is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with jsonopt.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import re
import numpy as np

import util

def variable(expression):    
    """
    parses variables or parameters and returns required values
    
    Parameters:
        expression:     string
        
    Returns:
        name:           string
        indexvalue:     list
        value:          numpy.array
        
    Example:
        (name,indexvalue,value)    = jsonopt.parse.variable('x[j] = 2 for j in range(10)')
        
        returns
        name: 'x'
        indexvalue: [0,1,2,3,4,5,6,7,8,9]
        value: numpy.array([2,2,2,2,2,2,2,2,2,2])
    """

    # check if there is a 'for' statement and parse it
    (content,loop,indexlist,indexvalue) = for_array_creation(expression)
    
    # check if the content contains a value
    (lhs,rhs,type) = equation(content)
    
    # parse the variable name by removing brackets
    name,varindexlist = indexed_expression(lhs)
        
    # parse the value
    value = []
    if rhs.lstrip().rstrip() != '':
        evalvars = dict(vars())
        evalvars.update(util.specialfunctions)
        
        if len(indexvalue)==0:
            value = eval(rhs,evalvars)
        else:
            value = np.array( eval('[ '*len(loop) + rhs + ' ' + ' ] '.join(loop[::-1]) + ' ]',evalvars) )
    
    return (name,indexvalue,value)    

    
def for_array_creation(expression):
    """
    look for an array creating " for  in " keywords in a string and return usefull values
    
    Parameters:
        expression:     string
        
    Returns:
        content:        string, the part which is repeated by the for statements
        loop:           list, a list of the for statements as strings
        indexlist:      list, a list of all index names as strings
        indexvalue:     list, a list of all values of the indices as tuples
        
    Example:
        (content,loop,indexlist,indexvalue) = jsonopt.parse.for_array_creation('x[i,j,k] for i in range(2) for j in range(3) for k in range(4)')
        
        returns
        content: 'x[i,j,k]'
        loop: ['for i in range(2)', 'for j in range(3)', 'for k in range(4)']
        indexlist: ['i','j','k']
        indexvalue: [(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 1, 0), (0, 1, 1), (0, 1, 2), (0, 1, 3), (0, 2, 0), (0, 2, 1), (0, 2, 2), (0, 2, 3), (1, 0, 0), (1, 0, 1), (1, 0, 2), (1, 0, 3), (1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 2, 0), (1, 2, 1), (1, 2, 2), (1, 2, 3)]
    """
    
    loop = []
    indexlist = []
    indexvalue = []
    
    # find (  ) statements
    bracepos = matching_braces(expression,['(',')'])
    
    # find 'for  in' statements
    forpos = [p.start(0) for p in re.finditer('for .*? in ',expression)]
    
    # check if the for loop is inside braces and ignore it if so
    tempforpos = []
    for p in forpos:
        add = True
        for b in bracepos:
            if b[0] <= p and p <= b[1]:
                add = False
                break
        if add:
            tempforpos.append(p)
    
    forpos = tempforpos
    
    
    # split the expression
    if len(forpos) < 1:
        content = expression.rstrip().lstrip()
    else:
        content = expression[:forpos[0]].rstrip().lstrip()
        
        for p in forpos[::-1]:
            curloop = expression[p:].rstrip().lstrip()
            loop.append( curloop )
            
            curindex = re.findall('for (.*?) in', curloop)[0].rstrip().lstrip()
            indexlist.append( curindex )
            
            #indexvalue.append( eval( '['+ curindex + ' ' + curloop +']') )
        
            # remove the loop from the expression
            expression = expression[:p]

        # reverse the lists
        loop = loop[::-1]
        indexlist = indexlist[::-1]
        #indexvalue = indexvalue[::-1]
        
        # get the indexvalue
        evalvars = dict(vars())
        evalvars.update(util.specialfunctions)
        indexvalue = eval( '[('+ ','.join(indexlist) + ')' + ' '.join(loop) +']', evalvars)
            
    return content,loop,indexlist,indexvalue
    
def indexed_expression(expression):
    """
    parse an indexed expression into the variable and a list of indices
    
    Parameters:
        expression:       string, the expression
        
    Returns:
        variable:         string, the variable which is indexed
        indexlist:        list, a list of index strings
        
    Example:
        (variable,indexlist) = jsonopt.parse.indexed_expression('x[i,j]')
        
        returns
        variable: 'x'
        indexlist: ['i','j']
    """
    
    left_bracket = expression.find('[')
    right_bracket = expression.find(']')
    if left_bracket > -1:
        variable = expression[:left_bracket].lstrip().rstrip()
        indexlist = [i.lstrip().rstrip() for i in expression[left_bracket+1:right_bracket].split(',')]
    else:
        variable = expression.lstrip().rstrip()
        indexlist = []
    
    return (variable,indexlist)

    
def equation(expression):
    """
    parse an equation expression into left hand side, right hand side and equation type
    
    Parameters:
        expression:    string, the expression
        
    Returns:
        lhs:           string, the left hand side
        rhs:           string, the right hand side
        type:          string, G -> Greater than or equal, L -> Less than or equal, E -> Equal
        
    Example:
        (lhs,rhs,type) = jsonopt.parse.indexed_expression('x[i,j] = y[i]')
        
        returns
        lhs: 'x[i,j]'
        rhs: 'y[i]'
        type: 'E'
    """
    
    eqpos = expression.find('=')
    gepos = expression.find('>=')
    lepos = expression.find('<=')
    
    if gepos > 0:
        lhs = expression[:gepos]
        rhs = expression[gepos+2:]
        type = 'G'
    elif lepos > 0:
        lhs = expression[:lepos]
        rhs = expression[lepos+2:]
        type = 'L'
    elif eqpos > 0:
        lhs = expression[:eqpos]
        rhs = expression[eqpos+1:]
        type = 'E'
    else:
        lhs = expression
        rhs = ''
        type = ''
        
    return (lhs,rhs,type)    
    
    
def matching_braces(expression,braces):
    """
    finds the matching braces or brackets in a string
    
    Parameters:
        expression:     string, the expression to find braces in
        braces:         list with 2 strings, starting and ending brace
    
    Returns:
        pairs:          list, list with pairs of indices of brace positions in the expression
    
    Example:
        pairs = jsonopt.parse.matching_braces('x[i,j] = sum(a+b for a in range(i) for b in range(j)) for i in range(2) for j in range(3)',['(',')'])
        
        returns
        pairs: [[12, 52], [31, 33], [49, 51], [68, 70], [86, 88]]
    """
    
    openpos = [p.start(0) for p in re.finditer(re.escape(braces[0]),expression)]
    closepos = [p.start(0) for p in re.finditer(re.escape(braces[1]),expression)]
    
    openclosepos = [p.start(0) for p in re.finditer(re.escape(braces[0])+'|'+re.escape(braces[1]),expression)]
    
    pairs = []
    for i,o in enumerate(openclosepos):
        if o in openpos:
            num_open = 0
            num_close = 0
            
            for c in openclosepos[i:]:
                if c in openpos:
                    num_open = num_open+1
                if c in closepos:
                    num_close = num_close+1
                    
                if num_open == num_close:
                    pairs.append([o,c])
                    break
    
    return pairs
    