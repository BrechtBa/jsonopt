jsonopt
-------

A set of classes to parse optimization problems from a JSON representation.
Pyomo is used in the background

Installation
============

Prequisites
^^^^^^^^^^^
* numpy: `<http://www.numpy.org/>`_
* pyomo: `<http://www.pyomo.org/>`_
* an optimization solver: 
   `ipopt <https://projects.coin-or.org/Ipopt>`_, `glpk <https://www.gnu.org/software/glpk/>`_, `IBM CPLEX <https://www-01.ibm.com/software/commerce/optimization/cplex-optimizer/>`_,...

Setup
^^^^^
* download the latest `release <https://github.com/BrechtBa/jsonopt/releases>`_
* unzip and cd to the folder
* run ``python setup.py install``


Examples
========

An optimization problem can be defined using a JSON text format by specifying the variables, parameters, objective and constraints::

    {
        "variables":[
            "Reals x[j] for j in range(4)"
        ],
        "parameters": [
            "A = 25",
            "B = 40",
            "C = 1",
            "D = 5"
        ],
        "objective": 
            "x[0]*x[3]*(x[0]+x[1]+x[2])+x[2]",
        "constraints":[
            "x[0]*x[1]*x[2]*x[3] >= A",
            "x[0]**2+x[1]**2+x[2]**2+x[3]**2 = B",
            "x[j] >= C for j in range(4)",
            "x[j] <= D for j in range(4)"
        ]
    }

    
jsonopt can parse this problem format and generate a problem inscance. Save the above formulation in a file ``json/hs071.json`` and in python run::
     
    import jsonopt
    
    with open('json/hs071.json', 'r') as jsonfile:
        jsonstring=jsonfile.read()
    
    problem = jsonopt.Problem(jsonstring=jsonstring)

the problem can be solved using an installed solver, by default jsonopt uses ipopt::

    problem.solve()
    
values can be retrieved in a ditionary or represented as a JSON string::

    values = problem.get_values()
    json_values = problem.get_json_values()
    
    
For more examples, check the `examples <https://github.com/BrechtBa/jsonopt/tree/master/examples/>`_ folder

Documentation
=============
Check the docstrings::
    
    import jsonopt
    help(jsonopt)