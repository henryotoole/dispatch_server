# test_cmd.py
# Josh Reed 2020
#
# Run all test scripts for the_root.

import os

# Import the core test extension
from henryotoole_utils.testing import test_extension

# Import any test scripts we wish to register with the test extension. These will
# be automatically registered on import.

from tests import t_dispatch
from tests import t_dispatch_flask

test_extension.test_module("dispatch")

test_extension.test_module("dispatch_flask")