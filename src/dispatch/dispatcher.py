# /dispatch_server/dispatch/dispatcher.py
# Josh Reed 2020
#
# This is the core class of dispatch. This class is intended to be instantiated just once.
# All functions registered as 'callable' will be remembered and accessed here.

# Imports:
# Our code
from dispatch import dispatch_callable_function
from dispatch import DispatchResponseResult, DispatchResponseError, DispatchResponseErrorExc, T_JSON, T_STRING
import dispatch.arg_types as arg_types

# Other libraries
import pendulum

# Base python
import json

class Dispatcher:

	FUNCTION_EXPIRE_TIME = 60*60*12 # Expire function calls after 12 hours.

	def __init__(self, redis_instance=None):
		"""Instantiate the dispatcher object. This should only be done once per server instance.

		redis_instance (Redis, optional): An instance of a python Redis server. This only required if dispatch is
			going to be used to make calls to clients (as opposed to receiving calls *from* clients).
		"""

		# List of all registered server functions.
		''' Format:
			{
				fname: {
					'fn': wrapped functionn
				}
			}
		'''
		self.server_fns = {}
		# List of all registered poll callback functions.
		# Note that we don't have to use REDIS for this (like we do for frontend calls) because
		# any polling is done within the scope of a single dispatch memory instance.
		''' Format:
			{
				namespace_string: [
					{
						'fn': wrapped function,
						'interval': interval in seconds,
						'last_called': int timestamp
					},
					{
						'fn': wrapped function,
						'interval': interval in seconds,
						'last_called': int timestamp
					}
				]
			}
		'''
		self.poll_callback_fns = {}

		self._redis = None

		if redis_instance is not None:
			self.setup_redis(redis_instance)

		# Bind the polling function that clients will query for updates
		self.bind_polling_function()

	def setup_redis(self, redis_instance):
		"""This function will attach a redis instance to this dispatcher, enabling the use of fn_foreign_call().

		Args:
			redis_instance (Redis): A python Redis server instance.
		"""
		self._redis = redis_instance

	def bind_polling_function(self):
		"""Set up the polling function which can be reached by the clients using the general
		dispatch infrastructure.
		"""

		@dispatch_callable_function(self, [T_STRING, T_STRING])
		def __dispatch__client_poll(session_id, client_name):
			"""Called every so often by a client that is engaged in 2 way communication with this
			dispatch server.

			Args:
				session_id (str): The session ID of the client which is polling
				client_name (str): The namespace this client is operating under
			"""
			return self.client_poll(session_id, client_name)

	def client_poll(self, session_id, client_name):
		"""Called every so often by a client that is engaged in 2 way communication with this
		dispatch server.

		Args:
			session_id (str): The session ID of the client which is polling
			client_name (str): The namespace this client is operating under

		Returns:
			dict: {
				'queued_functions': [{
					'fname': fname,
					'args': args,
					}, {...}, ...],
			}
		"""
		self.on_foreign_poll(session_id, client_name)
		return {'queued_functions': self.fn_foreign_get_calls_for_client(session_id)}

	def fn_polling_callback_register(self, fn, interval=0, namespace='*'):
		"""Register a function to be called whenever a client polls.

		Args:
			fn (function): The wrapped function to be executed with args (session_id, client_name)
			interval (int, optional): Length of time (in seconds) between callbacks if the client is polling
				regularly. Default is 0, which means 'as fast as possible'.
			namespace (str, optional): The namespace to operate under. If provided, this will ensure
				that the callback is only called for client polls operating under this namespace.
		"""
		namespace_block = self.poll_callback_fns.get(namespace, [])
		namespace_block.append({
			'fn': fn,
			'interval': int(interval),
			'last_called': 0
		})
		self.poll_callback_fns[namespace] = namespace_block

	def fn_server_register(self, fname, fn, arg_blocks, n_required):
		"""Register a universally-callable function with Dispatcher using its decorator instance.

		Args:
			fname (str): The function name. This must be unique
			fn (function): The wrapped function
			arg_blocks (list): A list of argument blocks which are of form {
					name: the argument name,
					arg_type: the argument type (string, see dispatch.arg_types),
					required: 1 or 0 depending on whether this is a kwarg
				}... if this is None, then we won't validate types for this function.
			n_required (int): The number of required arguments for this function
		"""
		self.server_fns[fname] = {
			'fn': fn,
			'arg_blocks': arg_blocks,
			'n_required': n_required
		}

	def fn_server_call(self, session_id, fname, provided_args):
		"""Call a registered server function with args.

		Args:
			session_id (str): The session ID of the foreign client making this call
			fname (str): Function name
			provided_args (list): A list of arguments to attempt to apply to the function.

		Returns:
			DispatchResponse: Either a result or an error response. In the case of a result response,
			the returned results data block will be the output of the called function.
		"""
		fn_block = self.server_fns.get(fname)

		# Check that a function of this name has been registered
		if fn_block is None:
			return DispatchResponseError.get_standard_error(
				session_id,
				DispatchResponseError.EC_METHOD_NOT_FOUND
			)

		fn = fn_block.get('fn')
		arg_blocks = fn_block.get('arg_blocks')
		n_required = fn_block.get('n_required')

		# Ensure we've provided sufficient args to fill all required (non kw) args
		if( n_required is not None) and (len(provided_args) != n_required):
			return DispatchResponseError.get_standard_error(
					session_id,
					DispatchResponseError.EC_INVALID_PARAMS,
					{'info': 'Function ' + str(fname) + ' requires ' + str(n_required) + ' parameters (' + str(len(provided_args)) + ' provided).'} 
				)

		args_to_process = []

		# If arg_blocks is None, then this call has been configured to ignore argument types.
		if arg_blocks is not None:
			# Ensure we actually have the correct args 
			for ii in range(len(arg_blocks)):
				arg_block = arg_blocks[ii]
				arg_type = arg_block.get('arg_type')
				arg_name = arg_block.get('name')
				arg_is_required = arg_block.get('required')
				required_arg_defs = arg_types.type_to_def_map[arg_type]
				provided_arg = provided_args[ii]

				# If arg is a kwarg, we don't worry about it.
				if arg_is_required == 0:
					continue
				
				# Arg is required, so let's check if the type is correct. If it's not, we return an error.
				# Make sure that it matches at least one of the required definitions. JSON, for instance,
				# can be a dict or a list
				at_least_one_match = False
				for required_arg_def in required_arg_defs:
					if isinstance(provided_arg, required_arg_def):
						at_least_one_match = True
						break
				if not at_least_one_match:
					return DispatchResponseError.get_standard_error(
						session_id,
						DispatchResponseError.EC_INVALID_PARAMS,
						{'info': 'Provided argument for "' + str(arg_name) + '" (' + str(provided_arg) + ') is not of type "' + str(required_arg_def) + '"'} 
					)

				args_to_process.append(provided_arg)
		else:
			args_to_process = provided_args

		# Validation is complete. Now call the function with the required arguments.
		try:
			fn_return = fn(*args_to_process)
		# If we raise a DispatchResponseErrorExc, we want to just return the DispatchResponseError
		except DispatchResponseErrorExc as e:
			return e.response

		# Return either the function return or the resultified function return.
		if isinstance(fn_return, DispatchResponseResult) or isinstance(fn_return, DispatchResponseError):
			return fn_return
		else:
			if fn_return is None:
				fn_return = {}
			return DispatchResponseResult(session_id, fn_return)

	def fn_server_get_all_names(self):
		"""Get all registered server function names as a list.

		Returns:
			list: List of string available server method names
		"""
		return list(self.server_fns.keys())

	def _fn_foreign_call(self, session_id, fname, *args):
		"""Call a foreign dispatch session function.

		Function calls added in this way will be 'stacked' in a memcache until the foreign client performs
		a poll and checks for any calls. When the client executes the calls it will NOT neccessarily execute
		them in the order they have been stacked.

		If the exact same call with the exact same arguments is added twice between client polls then the second
		call will be ignored.

		Args:
			session_id (str): Dispatch session id
			fname (str): The name of the client function
		"""
		if self._redis is None:
			raise ValueError("Dispatch cannot make foreign calls because no redis server has been registered with this dispatcher. See docs for setup_redis() for more info.")
		
		# Codify all data needed to execute function into this function block and stringify it.
		function_block = {
			'fname': fname,
			'args': args
		}
		function_block_string = json.dumps(function_block)

		key_name = self.fn_foreign_get_redis(session_id)
		
		# Adding to a redis set will never add the same string if it already exists
		self._redis.sadd(key_name, function_block_string)
		self._redis.expire(key_name, Dispatcher.FUNCTION_EXPIRE_TIME)

	def fn_foreign_call(self, session_id, fname, *args):
		"""Call a foreign dispatch session function.

		Args:
			session_id (str): Dispatch session id
			fname (str): The name of the client function
		"""
		return self._fn_foreign_call(session_id, fname, *args)

	def fn_foreign_get_calls_for_client(self, foreign_session_id):
		"""Get all function blocks which have been queued up for the provided client to execute next time
		it polls the server.

		This will clear the stack of functions.

		Args:
			foreign_session_id (str): The foreign client's session ID

		Returns:
			list: A list of function block dicts of form {
				'fname': fname,
				'args': args
			}
		"""
		if self._redis is None:
			return []

		key_name = self.fn_foreign_get_redis(foreign_session_id)

		call_strings = list(self._redis.smembers(key_name))

		# Gather all function blocks into a true data object
		function_blocks = []
		for call_string in call_strings:
			function_block = json.loads(call_string)
			function_blocks.append(function_block)

		# Remove all info in the set
		self._redis.delete(key_name)
		
		return function_blocks

	def fn_foreign_get_redis(self, foreign_session_id):
		"""Get the redis key for a specific session's command stack

		Args:
			foreign_session_id (str): The foreign session ID
		"""
		return "__dispatch__cstack_" + str(foreign_session_id)

	def on_foreign_query(self, session_id, permanent_data):
		"""Called whenever a foreign client makes any sort of query.

		Args:
			session_id (str): The foreign client ID
			permanent_data (dict): Any permanent data attached to the foreign client
		"""
		# In the future we'll use this to call any on_query callbacks.
		pass

	def on_foreign_poll(self, session_id, client_name):
		"""Called whenever a foreign client makes a poll. This function handles calling any custom hooks for
		client polling.

		Args:
			session_id (str): The foreign client ID
			client_name (str): The namespace this client is operating under
		"""
		callbacks = self.poll_callback_fns.get(client_name, [])
		callbacks = callbacks + self.poll_callback_fns.get('*', [])
		now_ts = pendulum.now().int_timestamp

		# Loop through all callbacks and execute any which have not been called back recently enough
		for callback in callbacks:
			interval = callback['interval']
			last_called = callback['last_called']
			if (now_ts - last_called) > interval:
				callback['fn'](session_id, client_name)
				callback['last_called'] = now_ts