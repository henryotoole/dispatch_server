# dispatch/dispatch/responses.py
# Josh Reed 2020
#
# This class can be used to construct JSONRPC-valid responses.

class DispatchResponse:

	def __init__(self, session_id, result=None, error=None):
		"""Create a new dispatch response. This will be a success or error response depending on whether
		result or error is provided. Both should never be provided.

		Args:
			session_id (str): The session ID of the client we are responding to.
			result (dict, optional): The result object. Pure custom. Defaults to None.
			error (dict, optional): The error object. Must be properly formatted. Defaults to None.
		"""
		self.session_id = session_id
		self.result = result
		self.error = error

	def get_json(self):
		"""Return this Dispatch as a JSON.
		"""
		json_data = {
			'id': self.session_id,
			'jsonrpc': '2.0'
		}

		if(self.result is not None):
			json_data['result'] = self.result

		if(self.error is not None):
			json_data['error'] = self.error

		return json_data

	def __str__(self):
		out = ""
		if(self.result is not None):
			out = "Result response for session '" + str(self.session_id) + "' with " + str(self.result)

		if(self.error is not None):
			out = "Error response for session '" + str(self.session_id) + "' with " + str(self.error)

		return out

	def __repr__(self):
		return self.__str__()

class DispatchResponseResult(DispatchResponse):

	def __init__(self, session_id, result={}):
		"""Create a result type (as opposed to the error type) dispatch response.

		Args:
			session_id (str): The session ID of the client we are responding to.
			result (dict, optional): The result dict, something custom. If not provided, empty dict.
		"""
		super().__init__(session_id, result=result)

class DispatchResponseError(DispatchResponse):

	# The following are JSONRPC-defined errors that can be returned.

	EC_PARSE_ERROR = -32700
	EC_INVALID_REQUEST = -32600
	EC_METHOD_NOT_FOUND = -32601
	EC_INVALID_PARAMS = -32602
	EC_INTERNAL_ERROR = -32603

	def __init__(self, session_id, error_code, error_message, error_data=None):
		"""Create a error type (as opposed to the result type) dispatch response.

		Args:
			session_id (str): The session ID of the client we are responding to.
			error_code (int): An integer error code. This should not be between -32700 and -32000 because
				the RPCJSON specs use those
			error_message (str): A short, concise message regarding the nature of the error. Should be about
				a sentence.
			error_data (dict, optional): Some optional data to describe the error. This is not required.
		"""

		error_block = {
			'code': error_code,
			'message': error_message
		}
		if error_data is not None:
			error_block['data'] = error_data

		super().__init__(session_id, error=error_block)

	@classmethod
	def _get_standard_error_messages(ClassDef):
		"""Get the standard error messages as defined by JSONRPC

		Returns:
			dict: {error_code: error_message, ...}
		"""
		std_error_messages = {}
		std_error_messages[DispatchResponseError.EC_PARSE_ERROR] = "Invalid JSON received by the server."
		std_error_messages[DispatchResponseError.EC_INVALID_REQUEST] = "The JSON sent is not a valid Request object."
		std_error_messages[DispatchResponseError.EC_METHOD_NOT_FOUND] = "The method does not exist or is not available."
		std_error_messages[DispatchResponseError.EC_INVALID_PARAMS] = "Invalid method parameter(s)."
		std_error_messages[DispatchResponseError.EC_INTERNAL_ERROR] = "Internal JSON-RPC error."
		
		return std_error_messages

	@classmethod
	def get_standard_error(ClassDef, session_id, error_code, error_data=None):
		"""Get one of the JSONRPC standard defined error responses. The error code provided here should
		be one of the statically defined EC_xxx codes at the top of this class.

		Args:
			session_id (str): The session ID of the client we are responding to.
			error_code (int): An integer error code. This should not be between -32700 and -32000 because
				the RPCJSON specs use those
			error_data (dict, optional): Some optional data to describe the error. This is not required.
		"""
		message = ClassDef._get_standard_error_messages().get(error_code)
		if message is None:
			raise ValueError("Error code " + str(error_code) + " is not a valid standard JSONRPC error code.")
		return ClassDef(session_id, error_code, message, error_data=error_data)
		