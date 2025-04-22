# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [TODO]

# TODO Change how tests are run to not use a custom method.
# TODO Add a convenience (and **documented** method to expose g.__dispatch__session_id)
# TODO Add actual documentation to class definitions and real docs. This is confusing even to me.

## [Unreleased]

## [0.5.0]

### Added
- gitignore, incredibly only now.

### Changed
- Refactor to pyproject.toml with '25 standard project structure and build mechanism
- Refactor such that dispatch can be installed via github link
- Port changelog to this standard format

## [0.4.2] 

### Fixed
- Fix a bug for when argument types are not specified.

## [0.4.0] 

### Changed
- 'Modernize' this package's install nature. Add pytest.ini and clean up setup.py.

## [0.3.5] 

### Changed
- Make non-returning functions return {} instead of None. Make exceptions raiseable

## [0.3.4] 

### Added
- Add 'list' to the list of types which are acceptable inputs to JSON arguments

## [0.3.3] 

### Fixed
- Fix an import that prevented permanent data from being decoded.

## [0.3.2] 

### Removed
- Remove a print statement

## [0.3.1] 

### Changed
- Switch to using inspect to determine function args so that wrapped functions can still be made into dispatch routes.

## [0.3.0] 

### Added
- Add polling callbacks

## [0.2.2] 

### Added
- Add method to allow a dispatch callable function to return a DispatchResponseError directly.

## [0.2.1] 

### Fixed
- Fix the __dispatch__get_functions method to not return a response object but rather the object itself. 

## [0.2.0] 

### Changed
- Refactor to ionel's src model

## [0.1.1] 

### Added
- Setup.py changes.

## [0.1.0] 

### Added
- The first fully tested version of dispatch

# Changelog:
# 0.1.0
#	The first fully tested version of dispatch
# 0.1.1
# 	Learning more about setup
# 0.2.0
#	Swtich to ionel's src model
# 0.2.1
#	Fix the __dispatch__get_functions method to not return a response object but rather the object itself. 
# 0.2.2
#	Add method to allow a dispatch callable function to return a DispatchResponseError directly.
# 0.3.0
# 	Add polling callbacks
# 0.3.1
#	Switch to using inspect to determine function args so that wrapped functions can still be made into
#	dispatch routes.
# 0.3.2
#	Remove a print statement
# 0.3.3
#	Fix an import that prevented permanent data from being decoded.
# 0.3.4
#	Add 'list' to the list of types which are acceptable inputs to JSON arguments
# 0.3.5
#	Make non-returning functions return {} instead of None. Make exceptions raiseable
# 0.4.0
#	'Modernize' this package's install nature. Add pytest.ini and clean up setup.py.
# 0.4.2
#	Fix a bug for when argument types are not specified.