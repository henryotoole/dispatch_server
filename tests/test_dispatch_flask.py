# dispatch_server/tests/t_dispatch_flask.py
# Josh Reed 2020
#
# Test all things relating to the base dispatch library.

# Our imports
from tests.resource_flask_test_lib import FlaskTestServer
from tests.resource_test_flask_app import FlaskUser
from dispatch_client_py.dispatch_client_test import DispatchClientTest, DispatchClientTestBlock
from dispatch_client_py.exceptions import DispatchResponseErrorException
from dispatch_client_py.exceptions import DispatchClientException

from dispatch_flask import DispatcherFlask

# Other libraries
from redis import Redis
import pytest

# python imports
import os
import json

base_url = 'http://localhost'
base_url_port = base_url + ":5000"

@pytest.fixture
def test_flask_app(scope='module'):
	"""Create a fixture which represents the flask test server running a flask app

	Yields:
		FlaskTestServer: A flask app instance
	"""

	import tests.resource_test_flask_app
	from tests.resource_test_flask_app import app

	test_server = FlaskTestServer()
	test_server.setup_dev_server(app, base_url)

	yield test_server

	test_server.dev_server_stop()

def test_basic(test_flask_app):
	"""Test the ability to make a simple dispatch function call.
	"""

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

def test_prewrapped(test_flask_app):
	"""Test that a pre-wrapped function will still be dispatch-routable.
	"""
	pass

def test_security(test_flask_app):
	"""Test the ability to call a dispatch route protected behind a login_required block.
	"""

	# This should fail
	test_client = DispatchClientTest(base_url_port)
	block = DispatchClientTestBlock('test_fn_dispatch_login', [1], desired_error=DispatchClientException)

	test_client.assert_block(block)

	# Now log it in, and we should succeed
	test_client.login_user("/login_login", FlaskUser.USER_EMAIL, FlaskUser.USER_PASS)

	block = DispatchClientTestBlock('test_fn_dispatch_login', [1], desired_result=True)

	test_client.assert_block(block)

def test_foreign_call(test_flask_app):
	"""Test the ability to request a call to this foreign client.
	"""

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