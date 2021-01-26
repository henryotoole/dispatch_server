# dispatch_server/tests/t_dispatch.py
# Josh Reed 2020
#
# Test all things relating to the base dispatch library.

# Our imports
from henryotoole_utils.testing import test_function
from dispatch import Dispatcher, DispatchResponseResult, DispatchResponseError
from dispatch import dispatch_callable_function
from dispatch import T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON

# Other libraries
from redis import Redis

# python imports
import os
import json

# Setup any ever-present variables for this run
redis_instance = Redis.from_url("redis://")
dispatcher_instance = Dispatcher(redis_instance=redis_instance)
test_sid = "test_session_id"

@test_function('dispatch', 'test_responses')
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


	return True


@test_function('dispatch', 'test_fn_server_call')
def test_fn_server_call():
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

	# Test the call with all data types.
	@dispatch_callable_function(dispatcher_instance, [T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON])
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

	args = [test_string, test_int, test_bool, test_float, test_json]
	response = dispatcher_instance.fn_server_call(test_sid, 'test_server_fn', args)

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

	# Ok, now test that same function but with bad arguments. This should return an error.
	args = [test_string, "a string", test_bool, test_float, test_json]
	response = dispatcher_instance.fn_server_call(test_sid, 'test_server_fn', args)
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
	response = dispatcher_instance.fn_server_call(test_sid, 'nonexist_function', args)
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
	@dispatch_callable_function(dispatcher_instance)
	def test_server_fn():
		return 1

	response = dispatcher_instance.fn_server_call(test_sid, 'test_server_fn', [])

	response_correct = {
		'id': test_sid,
		'jsonrpc': '2.0',
		'result': 1
	}

	assert response.get_json() == response_correct

	return True


@test_function('dispatch', 'test_fn_foreign_call')
def test_fn_foreign_call():
	"""Test the ability to add a foreign call to the queue.
	"""

	test_foreign_fname = "test_foreign_fn_name"
	test_arg_1 = "test_arg_1"
	test_arg_2 = 2

	# Check the basics: Can we register a foreign call and then pull it out of redis later?
	dispatcher_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)

	#Returns:
	#	list: A list of function block dicts of form {
	#		'fname': fname,
	#		'callback': callback_fname,
	#		'args': args,
	#		'kwargs': kwargs
	#	}

	fn_blocks = dispatcher_instance.fn_foreign_get_calls_for_client(test_sid)
	fn_blocks_correct = [
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_2]}
	]
	assert equal_ignore_order(fn_blocks, fn_blocks_correct)

	# A function registered multiple times should not just add unless the args have changed.
	dispatcher_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)
	dispatcher_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_2)
	# This one has a different second argument
	dispatcher_instance.fn_foreign_call(test_sid, test_foreign_fname, test_arg_1, test_arg_1)

	fn_blocks = dispatcher_instance.fn_foreign_get_calls_for_client(test_sid)
	fn_blocks_correct = [
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_2]},
		{'fname': test_foreign_fname, 'args': [test_arg_1, test_arg_1]}
	]
	
	assert equal_ignore_order(fn_blocks, fn_blocks_correct)

	return True


	

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