# dispatch_server/tests/t_dispatch.py
# Josh Reed 2020
#
# Test all things relating to the base dispatch library.

# FOR NOW we are going to use sys.path.insert here. When I get around to actually
# releasing dispatch and henryotoole_utils, I'll need to remove this and use 'pip install -e .'
# This will require giving both hutils and dispatch their own venv's...
# https://stackoverflow.com/questions/50155464/using-pytest-with-a-src-layer
# https://stackoverflow.com/questions/53378416/what-does-pipenv-install-e-do-and-how-to-use-it?noredirect=1&lq=1
import sys
sys.path.insert(0, "/the_root/projects/code_projects/dispatch/dispatch_server/src")

# Our imports
from dispatch import Dispatcher, DispatchResponseResult, DispatchResponseError, DispatchResponseErrorExc
from dispatch import dispatch_callable_function
from dispatch import T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON

# Other libraries
from redis import Redis
import pytest

# python imports
import os
import json
import time

# Setup any ever-present variables for this run
test_sid = "test_session_id"

@pytest.fixture
def dispatch_instance():
	"""Instantiate a dispatcher instance to test

	Yields:
		Dispatcher: A dispatcher instance connected to a generic redis server.
	"""

	redis_instance = Redis.from_url("redis://")
	dispatcher_instance = Dispatcher(redis_instance=redis_instance)
	yield dispatcher_instance

def test_responses():
	"""Test dispatch that dispatch responses can be generated correctly, both
	errors and results.
	"""
	test_data = {'test_key': 'test_val'}
	test_error_code = 1
	test_error_message = "test_error_msg"

	# Result with payload
	r_result = DispatchResponseResult(test_sid, test_data)
	r_result_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': test_data
	}

	assert r_result.get_json() == r_result_correct

	# Result without payload
	r_result = DispatchResponseResult(test_sid)
	r_result_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': {}
	}

	assert r_result.get_json() == r_result_correct

	# Error with payload
	r_result = DispatchResponseError(test_sid, test_error_code, test_error_message, test_data)
	r_result_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': test_error_code,
			'message': test_error_message,
			'data': test_data
		}
	}

	assert r_result.get_json() == r_result_correct

	# Error without payload
	r_result = DispatchResponseError(test_sid, test_error_code, test_error_message)
	r_result_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': test_error_code,
			'message': test_error_message
		}
	}

	assert r_result.get_json() == r_result_correct

	# Error with standard code
	r_result = DispatchResponseError.get_standard_error(
		test_sid,
		DispatchResponseError.EC_INVALID_REQUEST,
		test_data
	)

	r_result_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': DispatchResponseError.EC_INVALID_REQUEST,
			'message': DispatchResponseError._get_standard_error_messages()[DispatchResponseError.EC_INVALID_REQUEST],
			'data': test_data
		}
	}

	assert r_result.get_json() == r_result_correct

def test_fn_server_call_exception(dispatch_instance):
	"""Test that dispatch exceptions can be raised within a dispatch function and are returned rather than raised all the way.
	"""

	# Test the call with all data types.
	@dispatch_callable_function(dispatch_instance, [])
	def fn_raises_exc():
		# Make sure we can add a key to the json.
		err = DispatchResponseError(
			test_sid,
			0,
			'test_exception'
		)
		raise DispatchResponseErrorExc(err)

		# This should return the err, after all handling is done.

	response = dispatch_instance.fn_server_call(test_sid, 'fn_raises_exc', [])

	assert isinstance(response, DispatchResponseError)

def test_fn_server_call_return_nothing(dispatch_instance):
	"""Test that returning nothing returns an empty dict
	"""
	# Test the call with all data types.
	@dispatch_callable_function(dispatch_instance, [])
	def fn_return_nothing():
		pass

	response = dispatch_instance.fn_server_call(test_sid, 'fn_return_nothing', [])

	assert isinstance(response, DispatchResponseResult)
	assert response.result == {}

def test_fn_server_call(dispatch_instance):
	"""Test the ability to perform a server function call.
	
	This tests that;
		+ a callable function can be registered with a decorator
		+ all arg_types work
		+ an incorrect parameter will trip an error
		+ an uknown method will trip the correct error
		+ a callable function with NO parameters can be registered and called. 
	"""

	test_string = "test_string"
	test_int = 22
	test_bool = True
	test_float = 2.0121
	test_json = {'test_key': 'test_val'}
	test_json_list = ['thing1', 'thing2']

	# Test the call with all data types.
	@dispatch_callable_function(dispatch_instance, [T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON])
	def test_server_fn(ta_string, ta_int, ta_bool, ta_float, ta_json):
		# Make sure we can add a key to the json.
		ta_json['test_key2'] = 'test_val'
		return {
			'ta_string': ta_string,
			'ta_int': ta_int,
			'ta_bool': ta_bool,
			'ta_float': ta_float,
			'ta_json': ta_json,
		}

	# Test the call with all data types, but with list instead of dict
	@dispatch_callable_function(dispatch_instance, [T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON])
	def test_server_fn_list(ta_string, ta_int, ta_bool, ta_float, ta_json_list):
		return {
			'ta_string': ta_string,
			'ta_int': ta_int,
			'ta_bool': ta_bool,
			'ta_float': ta_float,
			'ta_json': ta_json_list,
		}

	args = [test_string, test_int, test_bool, test_float, test_json]
	response = dispatch_instance.fn_server_call(test_sid, 'test_server_fn', args)

	test_json['test_key2'] = 'test_val'
	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': {
			'ta_string': test_string,
			'ta_int': test_int,
			'ta_bool': test_bool,
			'ta_float': test_float,
			'ta_json': test_json,
		}
	}

	assert response.get_json() == response_correct

	# Check that we can also use a list json
	args = [test_string, test_int, test_bool, test_float, test_json_list]
	response = dispatch_instance.fn_server_call(test_sid, 'test_server_fn_list', args)

	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': {
			'ta_string': test_string,
			'ta_int': test_int,
			'ta_bool': test_bool,
			'ta_float': test_float,
			'ta_json': test_json_list,
		}
	}

	assert response.get_json() == response_correct

	# Ok, now test that same function but with bad arguments. This should return an error.
	args = [test_string, "a string", test_bool, test_float, test_json]
	response = dispatch_instance.fn_server_call(test_sid, 'test_server_fn', args)
	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': DispatchResponseError.EC_INVALID_PARAMS,
			'message': DispatchResponseError._get_standard_error_messages()[DispatchResponseError.EC_INVALID_PARAMS],
			'data': {
				'info': 'Provided argument for "ta_int" (a string) is not of type "<class \'int\'>"'
			}
		}
	}

	assert response.get_json() == response_correct

	# Ok, now test a function that does not exist
	args = [test_string]
	response = dispatch_instance.fn_server_call(test_sid, 'nonexist_function', args)
	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': DispatchResponseError.EC_METHOD_NOT_FOUND,
			'message': DispatchResponseError._get_standard_error_messages()[DispatchResponseError.EC_METHOD_NOT_FOUND]
		}
	}

	assert response.get_json() == response_correct

	# Test the call with no arguments
	@dispatch_callable_function(dispatch_instance)
	def test_server_fn():
		return 1

	response = dispatch_instance.fn_server_call(test_sid, 'test_server_fn', [])

	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': 1
	}

	assert response.get_json() == response_correct

def test_fn_server_call_exc(dispatch_instance):
	"""Test that server function calls that raise an exception are handled correctly.
	"""

	# Register the dispatch function to test
	@dispatch_callable_function(dispatch_instance, [])
	def test_server_fn():
		return DispatchResponseError(test_sid, 1, "test", {'key': 2})

	args = []
	response = dispatch_instance.fn_server_call(test_sid, 'test_server_fn', args)

	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'error': {
			'code': 1,
			'message': "test",
			'data': {'key': 2}
		}
	}

	assert response.get_json() == response_correct

def test_fn_foreign_call(dispatch_instance):
	"""Test the ability to add a foreign call to the queue.
	"""

	test_foreign_fname = "test_foreign_fn_name"
	test_arg_1 = "test_arg_1"
	test_arg_2 = 2

	# Check the basics: Can we register a foreign call and then pull it out of redis later?
	dispatch_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)

	#Returns:
	#	list: A list of function block dicts of form {
	#		'fname': fname,
	#		'callback': callback_fname,
	#		'args': args,
	#		'kwargs': kwargs
	#	}

	fn_blocks = dispatch_instance.fn_foreign_get_calls_for_client(test_sid)
	fn_blocks_correct = [
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_2]}
	]
	assert equal_ignore_order(fn_blocks, fn_blocks_correct)

	# A function registered multiple times should not just add unless the args have changed.
	dispatch_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)
	dispatch_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)
	# This one has a different second argument
	dispatch_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_1)

	fn_blocks = dispatch_instance.fn_foreign_get_calls_for_client(test_sid)
	fn_blocks_correct = [
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_2]},
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_1]}
	]
	
	assert equal_ignore_order(fn_blocks, fn_blocks_correct)

def test_fn_foreign_poll_callback(dispatch_instance):
	"""Test that the foreign poll callback system works
	"""
	memobj = {'named': 'not_fired', '*': 'not_fired'}

	# Register this polling callback.
	def test_poll_callback(session_id, client_name):
		memobj['named'] = 'fired'
	def test_poll_callback_general(session_id, client_name):
		memobj['*'] = 'fired'

	dispatch_instance.fn_polling_callback_register(
		test_poll_callback,
		interval=3,
		namespace='test_namespace'
	)
	dispatch_instance.fn_polling_callback_register(
		test_poll_callback_general
	)

	# Send a 'poll'
	dispatch_instance.fn_server_call(test_sid, '__dispatch__client_poll', [test_sid, 'test_namespace'])
	time.sleep(1)

	# The first poll should have triggered the function forboth
	assert memobj['named'] == 'fired'
	assert memobj['*'] == 'fired'
	memobj['named'] = 'not_fired'
	memobj['*'] = 'not_fired'

	dispatch_instance.fn_server_call(test_sid, '__dispatch__client_poll', [test_sid, 'test_namespace'])
	time.sleep(1)

	# The first poll should not have triggered the function for the namespace
	assert memobj['named'] == 'not_fired'
	# but should have for general
	assert memobj['*'] == 'fired'

	dispatch_instance.fn_server_call(test_sid, '__dispatch__client_poll', [test_sid, 'test_namespace'])
	time.sleep(2)
	dispatch_instance.fn_server_call(test_sid, '__dispatch__client_poll', [test_sid, 'test_namespace'])
	
	# The last poll should have triggered the function.
	assert memobj['named'] == 'fired'
	assert memobj['*'] == 'fired'
	memobj['named'] == 'not_fired'


def equal_ignore_order(a, b):
    """ Check if two lists contain equal members, regardless of order.
	
	Use only when elements are neither hashable nor sortable! """
    unmatched = list(b)
    for element in a:
        try:
            unmatched.remove(element)
        except ValueError:
            return False
    return not unmatched