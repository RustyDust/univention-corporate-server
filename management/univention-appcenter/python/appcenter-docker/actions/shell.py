#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for running commands in an app env
#
# Copyright 2015-2016 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#

import sys
import subprocess
import shlex
from argparse import REMAINDER

from univention.appcenter.actions import UniventionAppAction, StoreAppAction, Abort
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.utils import app_is_running


class Shell(UniventionAppAction, DockerActionMixin):
	'''Run commands within a docker app.'''
	help = 'Run in app env'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the app in whose environments COMMANDS shall be executed')
		parser.add_argument('commands', nargs=REMAINDER, help='Command to be run. Defaults to an interactive shell')

	def main(self, args):
		docker = self._get_docker(args.app)
		commands = args.commands[:]
		if not commands:
			commands = shlex.split(args.app.docker_shell_command)
		if not commands:
			raise Abort('Cannot run command: No command specified')
		if not app_is_running(args.app):
			raise Abort('Cannot run command: %s is not running in a container' % args.app.id)
		self.debug('Calling %s' % commands[0])
		docker_exec = ['docker', 'exec']
		tty = sys.stdin.isatty()
		if tty:
			docker_exec.append('-it')
		subprocess.call(docker_exec + [docker.container] + commands)
