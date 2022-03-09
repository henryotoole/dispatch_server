# dispatch/dec_fcall.py
# Josh Reed 2020
# 
# This is the decorator which is used to mark which functions are registered to dispatch. Such functions
# are callable from the foreign clients.

# Imports:
# Our code
from dispatch.arg_types import all_types

# Libraries

# Base python
import json
import urllib
from functools import wraps
import inspect

class dispatch_callable_function(object):

	def __init__(self, dispatcher_instance, arg_types=None):
		"""
		Set up the primary callable-function decorator for dispatch.

		CRITICAL NOTES:
		A)	This decorator must be the LAST (as in the highest in the order) decorator applied to a function. Due to
			the nature of this decorator it must capture a sort of 'snapshot' of the function we will be calling. There
			is no way to defer this action so it must be done last if the called function is going have it's other
			decorators fired. Thus, any decorators above this decorator over a function are entirely ignored.
		B)	Any decorators below (e.g. before) this one MUST preserve function signatures. These are things like the
			name, number of arguments, et. al. This can be done safely with the decorator module

		Args:
			dispatcher_instance (Dispatcher): The app-wide instance of the dispatcher object.
			arg_types (list, optional): A list of DispatchArgType instances which restrict the type of arguments
				allowable to this function. If left as None, then there will be no argument validation for this
				function on a variable-type basis (e.g. int, str, etc.)
		"""
		self.dispatcher_instance = dispatcher_instance 

		if arg_types is None:
			self.arg_types = None
		else:
			# Ensure the provided list of arg types is valid.
			for arg_type in arg_types:
				if not arg_type in all_types:
					raise ValueError("Invalid argument type '" + str(atype) + "' when constructing dispatch callable function.")
			self.arg_types = arg_types

	def __call__(self, f):
		"""
		If there are decorator arguments, __call__() is only called	once, as part of the decoration process! You can only give
		it a single argument, which is the function object.

		This function f (if decorated before the general_purpose_query decorator) MUST retain the base functions:
		+ name
		+ co_argcount
		+ co_varnames
		+ __defaults__
		In python 2 @functools.wraps() is insufficient to preserver this data. Python 3 supposedly fixes this.
		"""
		n_required = 0

		fname = f.__name__

		# If we are validating argument types for this wrapped function.
		if self.arg_types is not None:
			# The below method for doing this doesn't seem to care whether the function was previously wrapped!
			arg_blocks = []
			sig = inspect.signature(f)
			# This is an OrderedDict key/vals ('arg_name', <Parameter>)
			params = sig.parameters
			n_args = len(params)
			n_required = n_args

			if n_args != len(self.arg_types):
				raise ValueError("Dispatch-callable function '" + fname + "' has insufficient args. Ensure that pre-decorators preserved base function context.")
			
			try:
				x = 0
				for var_name, parameter in params.items():
					arg_block = {
						'name': var_name,
						'arg_type': self.arg_types[x],
						'required': 1
					}
					arg_blocks.append(arg_block)
					x += 1
			except IndexError:
				print("Function: " + str(fname))
				raise ValueError("Could not construct dispatch-callable functions because of argument mismatch.")
		else:
			arg_blocks = None
		
		@wraps(f)
		def wrapped_f(*args):
			return f(*args)

		self.dispatcher_instance.fn_server_register(fname, wrapped_f, arg_blocks, n_required)
		return wrapped_f
