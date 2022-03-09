# /dispatch_server/dispatch_flask/dispatcher_flask.py
# Josh Reed 2020
#
# This is an extension of the core dispatcher class with modifications so that it plays nicely with
# flask.

# Imports:
# Our code
from dispatch import Dispatcher
from dispatch_flask.routes import register_routes, register_special_methods

# Other libraries

# Base python

class DispatcherFlask(Dispatcher):

	def __init__(self, app=None, redis_instance=None, base_url="/_dispatch"):
		"""Instantiate the dispatcher object. This should only be done once per server instance.

		Args:
			app (Flask Application, optional): The flask application instance. If not provided here, init_app
				must be called later on before dispatcher is used.
			redis_instance (Redis, optional): An instance of a python Redis server. This only required if dispatch is
				going to be used to make calls to clients (as opposed to receiving calls *from* clients).
			base_url (str, optional): The base url endpoint. Defaults to "/_dispatch".
		"""
		super().__init__(redis_instance=redis_instance)

		self.base_url = base_url

		# This should be the last thing in this block
		if app is not None:
			self.init_app(app)
		

	def init_app(self, app):
		"""Setup this dispatcher with the app instance.

		Args:
			app (Flask Application): The flask application instance
		"""
		self.flask_app = app

		# If we wanted to modify app, we'd do it here.

		self.setup_routes_and_methods()
		

	def setup_routes_and_methods(self):
		"""This function is called after app has been attached to this class to set up all routes
		and methods used by Dispatcher.
		"""
		register_routes(self.flask_app, self, base_url=self.base_url)
		register_special_methods(self)