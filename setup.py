from setuptools import setup,find_packages

setup(
    name='json2ipopt',
    version='0.0.1',
    license='GNU GENERAL PUBLIC LICENSE',
	description='A class to parse non-linear programs in a json format and solve them using pyipopt',
	url='https://github.com/BrechtBa/json2ipopt',
	author='Brecht Baeten',
	author_email='brecht.baeten@gmail.com',
	packages=['json2ipopt'],
	install_requires=['ad'],
	classifiers = ['Programming Language :: Python :: 2.7'],
)