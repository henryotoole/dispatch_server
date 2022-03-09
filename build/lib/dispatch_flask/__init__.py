# dispatch/__init__.py
# Josh Reed 2020
#
# This is the module for the flask version of dispatch. This code can be instantiated like most
# flask modules with the init_app() function call.

from .dispatcher_flask import *
from .responses_flask import *
from .routes import *