from distutils.core import setup
from setuptools import find_packages

setup(
    name='parsenlp',
    version='0.1',
    license='GNU GENERAL PUBLIC LICENSE',
	description='A class to parse non linear programs and solve them using pyipopt',
    long_description=open('README.md').read(),
	url='https://github.com/BrechtBa/parsenlp',
	author='Brecht Baeten',
	author_email='brecht.baeten@gmail.com',
	packages=find_packages(),
	install_requires=['numpy','sympy','pyipopt'],
)