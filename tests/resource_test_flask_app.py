# dispatch_server/tests/resource_test_flask_app.py
# Josh Reed 2021
#
# This is a very basic flask application which is used to test the dispatch server.
#
# To use this, flask and flask_login must be installed and venv'd properly

# Our code
from dispatch_flask import DispatcherFlask
from dispatch import dispatch_callable_function
from dispatch import T_STRING, T_INT

# Other libraries
from redis import Redis

# Flask imports
import flask
import flask_login
from flask import Flask, jsonify, request, g
from flask_login import login_user, login_required

#Sets up the extensions and other path-containing files in this module
def setup():

	app.secret_key = b'aleksandr_solzhenitsyn'
	
	register_login(app)
	add_routes(app)
	register_dispatch(app)

def register_dispatch(app):
	"""Register the dispatcher instance. This will also register redis and some basic routes.
	"""

	redis_instance = Redis.from_url("redis://")

	# Ensure a redis server is available.
	redis_instance.set("_test_key", "val")

	dispatcher = DispatcherFlask(app, redis_instance)

	# Simple function which will return a value if the provided arg is a 2.
	@dispatch_callable_function(dispatcher, [T_INT])
	def test_fn_base(arg_int):
		if(arg_int == 2):
			return {'key': 'val'}
		else:
			return None

	# A function which will just return True but is login protected.
	@dispatch_callable_function(dispatcher, [T_INT])
	@login_required
	def test_fn_dispatch_login(arg_int):
		return True

	# A login-wrapped function with two variables (this caused problems in the past)
	@dispatch_callable_function(dispatcher, [T_INT, T_STRING])
	def test_fn_2arg(arg_int, arg_string):
		return True

	# A login-wrapped function with two variables (this caused problems in the past)
	@dispatch_callable_function(dispatcher, [T_INT, T_STRING])
	@login_required
	def test_fn_dispatch_login_2arg(yyyyarg_int, yyyyarg_string):
		return True

	# This function will place a foreign call to function 'test_foreign_function(1)' of the originating client
	@dispatch_callable_function(dispatcher)
	def test_fn_dispatch_foreign_call():
		# ID of the client who made this call
		session_id = g.__dispatch__session_id
		dispatcher.fn_foreign_call(session_id, 'test_foreign_function', 1)
		return {}


#We register extensions in this way to prevent circular import references. Simply provides a
#reference to 'app' to each extension.
def register_login(app):

	# Setup the login module
	login_manager = flask_login.LoginManager()
	login_manager.login_view = "login_login"
	login_manager.init_app(app)

	# Add the user loader function
	@login_manager.user_loader
	def load_user(user_id):
		return FlaskUser(user_id)

def add_routes(app):
	"""Add some routes for testing.
	"""

	# Register the login route
	@app.route('/login_login', methods=['GET', 'POST'])
	def login_login():
		email = request.values.get('email', type=str)
		password = request.values.get('password', type=str)
		if(email == FlaskUser.USER_EMAIL and password == FlaskUser.USER_PASS):
			user = FlaskUser(FlaskUser.USER_ID)
			login_user(user)
			return "", 200
		return "Bad login credentials", 403

	@app.route('/test_route', methods=['GET', 'POST'])
	def test_route():
		test_param = request.values.get('test_param', type=str)

		if(test_param == 'hello'):
			return jsonify({'key': 'val'}), 200
		else:
			return "did not say hello", 404

	@app.route('/test_login', methods=['GET', 'POST'])
	@login_required
	def test_login():
		return jsonify({}), 200



#This code is called whenever the module is imported
app = Flask(__name__)
setup()

class FlaskUser:

	USER_ID = 1
	USER_EMAIL = 'test_email'
	USER_PASS = 'test_pass'

	is_anonymous = False

	def __init__(self, user_id):
		"""Create a dummy flask user. For this server, there's only one user and it has
		a constant username and password.
		"""
		self.user_id = user_id

	def is_authenticated(self):
		return self.user_id == FlaskUser.USER_ID

	def is_active(self):
		return True
	
	def get_id(self):
		return self.user_id