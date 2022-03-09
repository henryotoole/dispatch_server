# dispatch/exceptions.py
# Josh Reed 2020
# 
# Exceptions used by the base dispatcher module.

from dispatch import DispatchResponseError

class DispatchResponseErrorExc(Exception):

	def __init__(self, response):
		"""Create a new exception to to represent a dispatch response error - useful when we don't want to bother
		with a chain of returns to bring a DispatchResponseError all the way back to the root dispatch function.

		Raising this exception within a dispatch request context will ultimately return the DispatchResponseError

		Args:
			response (DispatchResponseError): A filled-out dispatch response exception.
		"""
		if not isinstance(response, DispatchResponseError):
			raise ValueError("Response provided to exception is not type DispatchResponseError")
		message = response.error['message']
		super().__init__(message)

		self.response = response