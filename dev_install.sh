#!/bin/bash
# Josh Reed 2021
#
# An install script to install this dispatch server onto my system. MUST be run from dispatch_server director.
rm -rf dist build */*.egg-info *.egg-info
python setup.py install