# dispatch/exceptions.py
# Josh Reed 2020
# 
# Exceptions used by the base dispatcher module.

class IncompleteInitGPQException(Exception):
	"""Raised when ...
	"""

	def __init__(self, message):
		self.message = message
		super().__init__(self.message)