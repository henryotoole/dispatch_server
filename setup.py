# dispatch/dispatch_server/setup.py
# Josh Reed 2020
#
# This sets up the dispatch server module system wide. To install it run
# >> python setup.py install
from glob import glob

import setuptools
from setuptools import setup
from setuptools import find_packages

# Changelog:
# 0.1.0
#	The first fully tested version of dispatch
# 0.1.1
# 	Learning more about setup
# 0.2.0
#	Swtich to ionel's src model
# 0.2.1
#	Fix the __dispatch__get_functions method to not return a response object but rather the object itself. 
# 0.2.2
#	Add method to allow a dispatch callable function to return a DispatchResponseError directly.
# 0.3.0
# 	Add polling callbacks
# 0.3.1
#	Switch to using inspect to determine function args so that wrapped functions can still be made into
#	dispatch routes.
# 0.3.2
#	Remove a print statement
# 0.3.3
#	Fix an import that prevented permanent data from being decoded.
# 0.3.4
#	Add 'list' to the list of types which are acceptable inputs to JSON arguments
# 0.3.5
#	Make non-returning functions return {} instead of None. Make exceptions raiseable

# Kindly note:
# Given this setup.py, src is never ever mentioned by import or anything
# Import with 'import packagename'
# Cool right?
#
# ├─ src
# │  └─ packagename
# │     ├─ __init__.py
# │     └─ ...
# ├─ tests
# │  └─ ...
# └─ setup.py


# Master TODO for dispatch:
# USE THIS
# https://blog.ionelmc.ro/2014/05/25/python-packaging/

setup(
	# This is NOT the module name e.g. 'import dispatch_server'. This is the library name as
	# it would appear in pip etc.
	name='dispatch_server',
	version='0.3.5',
	license='GNUv3',
	description='A RPC server which follows JSONRPC 2.0 and allows for both client-to-server and server-to-client communication.',
	author='Josh Reed (henryotoole)',
	#author_email='email@the_root.tech',
	url='https://github.com/henryotoole/dispatch_server',
	packages=find_packages('src'),
	package_dir={'': 'src'},
	py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
	include_package_data=True,
	zip_safe=False,
	classifiers=[
		# TODO figure out these
		# complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
		#'Development Status :: 5 - Production/Stable',
		#'Intended Audience :: Developers',
		#'License :: OSI Approved :: BSD License',
		#'Operating System :: Unix',
		#'Operating System :: POSIX',
		#'Operating System :: Microsoft :: Windows',
		#'Programming Language :: Python',
		#'Programming Language :: Python :: 2.7',
		#'Programming Language :: Python :: 3',
		#'Programming Language :: Python :: 3.5',
		#'Programming Language :: Python :: 3.6',
		#'Programming Language :: Python :: 3.7',
		#'Programming Language :: Python :: 3.8',
		#'Programming Language :: Python :: 3.9',
		#'Programming Language :: Python :: Implementation :: CPython',
		#'Programming Language :: Python :: Implementation :: PyPy',
		# uncomment if you test on these interpreters:
		# 'Programming Language :: Python :: Implementation :: IronPython',
		# 'Programming Language :: Python :: Implementation :: Jython',
		# 'Programming Language :: Python :: Implementation :: Stackless',
		#'Topic :: Utilities',
	],
	keywords=[
		# eg: 'keyword1', 'keyword2', 'keyword3',
	],
	# We use python 3.6.3 lol
	python_requires='>=3.6.0, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
	#TODO
	install_requires=[
		# eg: 'aspectlib==1.1.1', 'six>=1.7',
	],
	#TODO
	extras_require={
		# eg:
		#   'rst': ['docutils>=0.11'],
		#   ':python_version=="2.6"': ['argparse'],
	},
	#TODO
	setup_requires=[
		'pytest-runner',
	],
	entry_points={
		'console_scripts': [
			'nameless = nameless.cli:main',
		]
	},
)