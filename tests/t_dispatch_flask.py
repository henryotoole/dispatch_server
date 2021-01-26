# dispatch_server/tests/t_dispatch_flask.py
# Josh Reed 2020
#
# Test all things relating to the base dispatch library.

# TEMPORARY, Remove after we proof the client
import sys
sys.path.insert(0, "/the_root/projects/code_projects/dispatch/dispatch_client_py")
from dispatch_client_py.dispatch_client_test import DispatchClientTest, DispatchClientTestBlock
from dispatch_client_py.exceptions import DispatchResponseErrorException, DispatchResponseTimeoutException
from dispatch_client_py.exceptions import DispatchClientException, DispatchServerException

# Our imports
from henryotoole_utils.testing import test_function
from henryotoole_utils.flask_test_server import FlaskTestServer
from dispatch import DispatchResponseResult, DispatchResponseError
from dispatch import dispatch_callable_function
from dispatch import T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON

from dispatch_flask import DispatcherFlask

# Other libraries
from redis import Redis

# python imports
import os
import json

base_url = 'http://localhost'
base_url_port = base_url + ":5000"

@test_function('dispatch_flask', 'test_basic_')
def test_basic():
	"""Test the ability to make a simple dispatch function call.
	"""

	import tests.resource_test_flask_app
	from tests.resource_test_flask_app import app
	test_server = FlaskTestServer()
	test_server.setup_dev_server(app, base_url)

	try:
		test_client = DispatchClientTest(base_url_port)

		# Check that things work like they should
		block = DispatchClientTestBlock('test_fn_base', [2], {'key': 'val'})
		test_client.assert_block(block)

		# Check that it complains if insufficient arguments
		block = DispatchClientTestBlock('test_fn_base', [], desired_error=DispatchResponseErrorException)
		test_client.assert_block(block)

		# Check that it complains if too many arguments
		block = DispatchClientTestBlock('test_fn_base', [4, 1], desired_error=DispatchResponseErrorException)
		test_client.assert_block(block)

		# Check that it complains wrong type of argument
		block = DispatchClientTestBlock('test_fn_base', ["Aleksandr"], desired_error=DispatchResponseErrorException)
		test_client.assert_block(block)
	except:
		test_server.dev_server_stop()
		raise
	test_server.dev_server_stop()

	return True

@test_function('dispatch_flask', 'test_security')
def test_security():
	"""Test the ability to call a dispatch route protected behind a login_required block.
	"""

	import tests.resource_test_flask_app
	from tests.resource_test_flask_app import app, FlaskUser
	test_server = FlaskTestServer()
	test_server.setup_dev_server(app, base_url)

	try:
		# This should fail
		test_client = DispatchClientTest(base_url_port)
		block = DispatchClientTestBlock('test_fn_dispatch_login', [], desired_error=DispatchClientException)

		test_client.assert_block(block)

		# Now log it in, and we should succeed
		test_client.login_user("/login_login", FlaskUser.USER_EMAIL, FlaskUser.USER_PASS)

		#block = DispatchClientTestBlock('test_fn_dispatch_login', [], desired_result=True)

		#test_client.assert_block(block)
	except:
		test_server.dev_server_stop()
		raise
	test_server.dev_server_stop()

	return True

@test_function('dispatch_flask', 'test_foreign_call')
def test_foreign_call():
	"""Test the ability to request a call to this foreign client.
	"""

	import tests.resource_test_flask_app
	from tests.resource_test_flask_app import app, FlaskUser
	test_server = FlaskTestServer()
	test_server.setup_dev_server(app, base_url)

	try:
		# The flags must be ref'd to an object for the scope to work out. Go figure.
		permaobject = {
			'function_execute_success': False,
			'function_execute_at_all': False
		}
		# This little block is called when we send the block
		def foreign_call_function(arg_1):
			permaobject['function_execute_at_all'] = True
			if(arg_1 == 1):
				permaobject['function_execute_success'] = True

		# This should succeed
		test_client = DispatchClientTest(base_url_port)
		test_client.client_bind_function(foreign_call_function, 'test_foreign_function')
		block = DispatchClientTestBlock('test_fn_dispatch_foreign_call', [], desired_result={})
		test_client.assert_block(block)

		# We need to run a poll
		test_client._polling_function()

		# Function above is called...
		if not permaobject['function_execute_at_all']:
			raise ValueError("Function did not execute.")
		if not permaobject['function_execute_success']:
			raise ValueError("Function executed but recieved wrong argument.")

	except:
		test_server.dev_server_stop()
		raise
	test_server.dev_server_stop()

	return True