# dispatch/dispatch_flask/routes.py
# Josh Reed 2020
# 
# This file defines all routes used by the flask dispatch server. Importing it does not register these
# routes - instead call register_routes() to do this.

# Imports:
# Our code
from dispatch_flask.responses_flask import dispatch_response_to_flask_response
from dispatch import DispatchResponseError, DispatchResponseResult, dispatch_callable_function

# Flask
from flask import g, request
import urllib
from werkzeug.wrappers import Response

# Base python
import json

def register_routes(app, dispatcher, base_url="/_dispatch"):
	"""Register the routes needed for this dispatch server to function.

	Args:
		app (Flask Application): The flask application instance
		dispatcher (DispatcherFlask): The dispatcher instance.
		base_url (str, optional): The base url endpoint. Defaults to "/_dispatch".
	"""
	@app.route(base_url, methods=["GET", "POST"])
	def _dispatch_primary_route():
		"""The primary connection point for all JSONRPC requests to this server.

		Args (required request params):
			jsonrpc (str): The jsonrpc standard version (should be 2.0)
			method (str): The name of the method we are calling
			params (str): A stringified JSON of the parameters in list form
			id (str): The session ID of the foreign client making this request.

		Aux args (non-required request params):
			__dispatch__permanent_data (str): A stringified JSON containing a key-value dict of 'permanent data'
				that is delivered with every request. This might, for instance, include validation info.

		Returns:
			flask.Response: A flask-valid response which will contain a JSON which adheres to JSONRPC response
				structure.
		"""
		# Unpack the jsonrpc-formatted data.
		jsonrpc = request.values.get("jsonrpc")
		fname = request.values.get("method")
		arg_jsonstring = request.values.get("params")
		session_id = request.values.get("id")

		# Set a session ID to the flask request context so it is accessible later on.
		g.__dispatch__session_id = session_id

		# Unpack any of the extra non-required stuff which might exist
		permanent_data = request.values.get("__dispatch__permanent_data")

		# Return a response error if the version is wrong.
		if not jsonrpc == '2.0':
			resp = DispatchResponseError.get_standard_error(
				session_id,
				DispatchResponseError.EC_INVALID_REQUEST,
				{'info': 'Bad JSONRPC version.'}
			)
			return dispatch_response_to_flask_response(resp)
		
		# Check to ensure all needed info has been provided.
		if fname is None or arg_jsonstring is None or session_id is None:
			resp = DispatchResponseError.get_standard_error(
				session_id,
				DispatchResponseError.EC_INVALID_REQUEST,
				{'info': 'Method, params, or id is missing.'}
			)
			return dispatch_response_to_flask_response(resp)

		# Check and see if permanent data has been provided.
		if permanent_data is not None:

			permanent_data = urllib.parse.unquote(permanent_data) # Decode URI Component
			
			try:
				permanent_data = json.loads(permanent_data) # Checks validitiy of json (ensure nothing malicious, at least)
			except Exception: # The JSON String was not valid.
				resp = DispatchResponseError.get_standard_error(
					session_id,
					DispatchResponseError.EC_PARSE_ERROR,
					{'info': 'The "permanent_data" encoded JSON string could not be parsed. Ensure it is urlencoded.'}
				)
				return dispatch_response_to_flask_response(resp)

		else:
			# By default make this an empty dict
			permanent_data = {}
		g.__dispatch__permanent_data = permanent_data
			
		# If we've made it this far, we should now attempt to process the method call

		# Unpack the params
		args = urllib.parse.unquote(arg_jsonstring) # Decode URI Component
		try:
			args = json.loads(args) # Checks validitiy of json (ensure nothing malicious, at least)
		except Exception: # The JSON String was not valid.
			resp = DispatchResponseError.get_standard_error(
				session_id,
				DispatchResponseError.EC_PARSE_ERROR,
				{'info': 'The "params" encoded JSON string could not be parsed. Ensure it is urlencoded.'}
			)
			return dispatch_response_to_flask_response(resp)

		# Alright, now call the server in dispatcher
		resp = dispatcher.fn_server_call(session_id, fname, args)

		# This might already be a Flask response object if the function was protected by @login_required.
		if isinstance(resp.result, Response):
			return resp.result

		# Make sure we notify central dispatcher that this foreign client has just checked in.
		dispatcher.on_foreign_query(session_id, permanent_data)
		
		return dispatch_response_to_flask_response(resp)

def register_special_methods(dispatcher):
	"""Uses the JSONRPC machinery provided by dispatch itself to make some functions which foreign
	clients will call to achieve certain auxilliary-to-JSONRPC behavior provided by dispatch (like
	foreign calls, polling, etc.)
	"""

	@dispatch_callable_function(dispatcher, [])
	def __dispatch__get_functions():
		"""Returns all functions registered to this server as callable from a frontend client.

		Returns:
			DispatchResponseResult: A standard response with the 'result' payload as a list of names.
		"""
		all_names = dispatcher.fn_server_get_all_names()
		return all_names