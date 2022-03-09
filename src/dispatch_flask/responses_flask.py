# dispatch/dispatch_flask/responses_flask.py
# Josh Reed 2020
#
# These classes can be used to construct JSONRPC-valid responses with some added functionality to make
# them behave well with flask

# Imports:
# Our code

# Flask
from flask import jsonify

def dispatch_response_to_flask_response(response):
	"""Convert a dispatch response to a flask response.

	Args:
		response (DispatchResponse): The dispatch response instance

	Returns:
		(flask.Response, int): The flask style response tuple with the Response, 200
	"""

	try:
		json_string = jsonify(response.get_json())
	except TypeError:
		print("The JSON in question:")
		print(response.get_json())
		raise
	
	return json_string, 200