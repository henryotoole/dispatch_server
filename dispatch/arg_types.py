# dispatch/arg_types.py
# Josh Reed 2020
#
# This file contains the standard argument types which are allowable for dispatch-bound functions.

T_STRING = "string",	# Any sort of string
T_INT = "int",			# A pure integer
T_BOOL = "int",			# This argument is for booleans. Note that it is really just int. Don't use 'true'/'false'
T_FLOAT = "float",		# A floating point number
T_JSON = "json"			# The argument is a stringified, urlencoded json

all_types = [T_STRING, T_INT, T_BOOL, T_FLOAT, T_JSON]
type_to_def_map = {}
type_to_def_map[T_STRING] = str
type_to_def_map[T_INT] = int
type_to_def_map[T_BOOL] = int
type_to_def_map[T_FLOAT] = float
type_to_def_map[T_JSON] = dict

# IF ANY OF THESE ARE CHANGED:
#	All foreign clients must have their lists updated as well.