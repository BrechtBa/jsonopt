import json2ipopt



with open('nlp.json', 'r') as jsonfile:
    jsonstring=jsonfile.read().replace('\n', '').replace('\t', ' ')
#jsonstring = r'{"variables":["T[i] for i in range(25)","P[i] for i in range(24)","Q[i] for i in range(24)","COP[i] for i in range(24)"]}'

problem = json2ipopt.Problem(jsonstring)