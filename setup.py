from setuptools import setup

setup(
    name='parseipopt',
    version='0.0.1',
    license='GNU GENERAL PUBLIC LICENSE',
	description='A class to parse non-linear programs in a json format and solve them using pyipopt',
	url='https://github.com/BrechtBa/parseipopt',
	author='Brecht Baeten',
	author_email='brecht.baeten@gmail.com',
	packages=['parseipopt'],
	install_requires=['ad'],
	classifiers = [],
)