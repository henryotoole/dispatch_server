# dispatch/dispatch_server/setup.py
# Josh Reed 2020

from setuptools import setup, find_packages
import os
import glob


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
# 0.4.0
#	'Modernize' this package's install nature. Add pytest.ini and clean up setup.py.
# TODO Change how tests are run to not use a custom method.

# Lessons from https://blog.ionelmc.ro/2014/05/25/python-packaging/

setup(
	# This is NOT the module name e.g. 'import dispatch_server'. This is the library name as
	# it would appear in pip etc.
	name='dispatch_server',
	version='0.4.0',
	license='GNUv3',
	description='A RPC server which follows JSONRPC 2.0 and allows for both client-to-server and server-to-client communication.',
	author='Josh Reed (henryotoole)',
	url='https://github.com/henryotoole/dispatch_server',
	packages=find_packages('src'),
	package_dir={'': 'src'},
	py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob.glob('src/*.py')],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		"flask",
		"flask_login",
		"redis"
	],
	classifiers=[
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python :: 3',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
	]
)