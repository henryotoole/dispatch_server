# dispatch_server/tests/resource_flask_test_lib.py
# Josh Reed 2020
#
# This utility allows a flask development server to be started and run in a parallel thread
# while a test script executes some sort of testing of code that lives on that flask server.
#
# I no longer use such involved testing forms - flask has it's own test infrastructure that
# I've since learned of. However, my tests for Dispatch still use this old way.

# Our code
from hacutils.misc import strip_unicode

# Base python
import requests
from functools import partial
import urllib, time
import json
import time, sys
from multiprocessing import Process
import traceback
import subprocess

class FlaskTestServer:

	"""This util sets up and runs a flask dev server in its own thread. Simple as that.
	"""

	def __init__(self):
		"""Instantiate the test server. It won't be launch until setup_dev_server() is called.
		"""

		# Setup blank dummies
		self.dummy_device = None
		self.dummy_frontend = None

		# Dev server stuff
		self.dev_server_process = None
		self.base_url = None

	def setup_dev_server(self, app, url):
		"""Setup the development server on this machine with the provided paths. To call this
		function you must have the correct virtualenv for this server loaded with:
			source .../venv/bin/activate

		Note that this function will take about 0.5 seconds to execute.

		Args:
			app (Flask Application): The flask server app (imported but without app.run() called)
			url (String): An absolute URL which points at this server. Like 'dev.theroot.tech'
				or perhaps 'localhost'
		"""

		# Kindly note: Starting with debug: False is VERY IMPORTANT. Otherwise two instances of the flask server launch.
		self.dev_server_process = Process(target=app.run, kwargs={'debug': False})
		self.dev_server_process.start()
		self.base_url = url
		time.sleep(0.5)

	def dev_server_stop(self):
		"""Stop the running flask dev server.
		"""
		if self.dev_server_process is not None:
			self.dev_server_process.terminate()
			self.dev_server_process.join()

class FlaskTestClient:

	def __init__(self, base_url):
		"""Instantiate a test client for a flask server (or any server really)

		Args:
			base_url (str): The base url for the server (like www.google.com)
		"""
		
		# Setup GPQ variables
		self.request_timeout = 10
		self.base_url = base_url
		# Dynamic dict of simple key/val pairs which will be sent as standard request parameters.
		self.all_route_base_data = {}

		# These cookies will be sent with every request.
		self._cookies = {}

	def login_user(self, login_route, user_email, user_pass):
		""" Calling this function will log in a user with user_email and user_password at the
		indicated server route. This assumes that flask_login or something similar has been
		used for this server.

		Calling this function will add the cookies returned by the login request to this
		client. Those cookies will be sent along with subsequent requests, simulating a logged
		in user in a browser or something.

		Args:
			login_route (str): The login route for this server e.g. "/login"
			user_email (str): The email of the user to log in with
			user_pass (str): The password of the user to log in with
		"""
		
		ret, data = self.get_json(self.base_url + login_route, {'email': user_email, 'password': user_pass})
		
		# Save the cookies off the login request so that we appear logged in every time.
		self._cookies = self._last_request.cookies

	def assert_block(self, block):
		"""Assert that a request block actually evaluates correctly when fired at a server.
		
		Raises:
			AssertionError if it does not.

		Args:
			block (FlaskAppRouteTestBlock): The block to test
		"""

		# Send the block request
		success, ret = self.send_post_request(block.route, block.request_data, block.file_paths)

		# Evaluate the response
		if not success:
			# The query did not return a 200. If a 200 was desired, this is wrong.
			if block.desired_code == 200:
				raise AssertionError(
					"Wrong return code for route '" + block.get_route_name() + "': wants (" + str(block.desired_code) + "), got (" + str(ret) + ")"
				)
			return
		else:
			# The query did return a 200
			# If we didn't want a 200, say something
			if block.desired_code != 200:
				raise AssertionError(
					"Wrong return code for route '" + block.get_route_name() + "': wants (" + str(block.desired_code) + "), got (" + str(ret) + ")"
				)
			# Otherwise we did want a 200, so check if we got the right data back.
			if block.desired_data is not None:
				desired_data = strip_unicode(block.desired_data)
				# == comparison here will check if the two dicts have the same keys and values (does not care about order)
				if not (desired_data == ret):
					raise AssertionError(
						"Wrong return data for route '" + block.get_route_name() + "' (200): wants (" + str(desired_data) + "), got (" + str(ret) + ")"
					)

	def send_post_request(self, route, data, file_paths=[]):
		"""Send a post request with the following characteristics:

		Args:
			route (str): App route like '/my_api/get_data'
			data (dict): List of key-val pairs to be sent along as request data.
			file_paths (list): A list of absolute paths to files to include in this request.
		Returns:
			tuple: success, backend_return.
			+ success is True if we got a 200-code back from the server and False otherwise.
			+ backend_return is whatever the server returns. Usually this is a dict. It's an HTTP error
			  code if success was False.
		"""
		data_copy = json.loads(json.dumps(data))
		for key, val in self.all_route_base_data.items():
			data_copy[key] = val
		
		# Attempt to load all requested file paths
		files = {}
		for ii in range(len(file_paths)):
			file_number = str(ii)
			files[file_number] = open(file_paths[ii], 'rb')


		# Actually lob the request
		r_code, r_data = self.get_json(self.base_url + route, data_copy, files=files)

		success = r_code == 200
		if(success):
			return True, r_data
		else:
			return False, r_code

	def get_json(self, url, data, files={}):
		"""This is a very rudimentary way to send a request to a url with POST key/value pairs and perhaps
		some files.

		Args:
			url (String): The absolute url at which to place this request
			data (Dict): A dictionary of key/value pairs to be sent to the server. All keys and values will be stringified
			files (dict, optional): Files to be sent with the request. Defaults to {}.
		
		Returns:
			Tuple: status_code, response_data e.g.    
				404, "File not found" or
				200, {'json_key', 1} <--- note that this is an actual dict, not a string.
			If the request times out, the tuple (None, None) is returned.
		"""
		r = requests.post(url, data=data, files=files, timeout=self.request_timeout, cookies=self._cookies)
		self._last_request = r
		if(r.status_code != 200):
			dtxt = r.text
			if len(dtxt) > 1164:
				dtxt = dtxt[0:1164]
			return r.status_code, dtxt # Return the status code and None to signify it wasn't a 200
		try:
			return 200, r.json() # Return the JSON and the 200 code
		except ValueError as e:
			return 200, None # No JSON parseable, but we still got a 200

		return None, None # Connection timed out, so no code or JSON

class FlaskAppRouteTestBlock():

	def __init__(self, route, desired_code, desired_data, request_data={}, file_paths=[]):
		"""Create a test block that can be used to assert whether a flask POST route performs correctly.
		Args:
			route (str): The route (from server domain) like '/my_api/get_data'
			desired_code (int): The desired return code of the request (e.g. 200, 404, etc)
			desired_data (dict): The desired value of the JSON data returned by this query. If None,
				this term will be ignored
			request_data (dict): The array of string key/value pairs to be sent as request parameters
			file_paths (list): A list of absolute paths to files to include in this request.
		"""

		self.route = route
		self.desired_code = desired_code
		self.desired_data = desired_data
		self.request_data = request_data
		self.file_paths = file_paths

	def get_route_name(self):
		return self.route

	def __repr__(self):
		return "App Route Test Block:  https://etc" + self.route + "?" + str(self.request_data) + " --> (" + str(self.desired_code) + "," + str(self.desired_data) + ")"
	
	def __str__(self):
		return self.__repr__()