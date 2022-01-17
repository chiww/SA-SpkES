# coding=utf-8
#
# Copyright © 2011-2015 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

""" Sets the packages path and optionally starts the Python remote debugging client.

The Python remote debugging client depends on the settings of the variables defined in _pydebug_conf.py.  Set these
variables in _pydebug_conf.py to enable/disable debugging using either the JetBrains PyCharm or Eclipse PyDev remote
debug egg which must be copied to your application's bin directory and renamed as _pydebug.egg.

"""

from __future__ import absolute_import, division, print_function, unicode_literals
import os
settrace = stoptrace = lambda: NotImplemented
remote_debugging = None


def initialize():

    from os import path
    from sys import modules, path as python_path

    import platform

    module_dir = path.dirname(path.realpath(__file__))
    system = platform.system()

    # -----------------------------------------------------------------------------------------
    # Add APP_HOME packages lib to sys.path
    splunkhome = os.environ['SPLUNK_HOME']
    python_path.append(os.path.join(splunkhome, 'etc', 'apps', 'SA-SpkES', 'lib'))
    python_path.append(os.path.join(splunkhome, 'etc', 'apps', 'SA-SpkES', 'bin', 'packages'))
    # -----------------------------------------------------------------------------------------

    for packages in path.join(module_dir, 'packages'), path.join(path.join(module_dir, 'packages', system)):
        if not path.isdir(packages):
            break
        python_path.insert(0, path.join(packages))

    return

initialize()
del initialize
