#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for freezing an app
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.
#

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.ucr import ucr_save


class Pin(UniventionAppAction):
    """
    Disables upgrades for this app. Also does not allow
    to remove this app. Useful when a newer app version
    is available, but due to issues with the new version the
    current version should not be upgraded or removed.
    """

    help = 'Pins or unpins an app version'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be pinned or unpinned')
        parser.add_argument('--revert', action='store_true', help='Unpin previously pinned app')

    def main(self, args):
        if not args.app.is_installed():
            self.fatal('%s is not installed!' % args.app.id)
            return
        if args.revert:
            self._unpin(args.app)
        else:
            self._pin(args.app)

    def _unpin(self, app):
        ucr_save({app.ucr_pinned_key: None})

    def _pin(self, app):
        ucr_save({app.ucr_pinned_key: 'true'})
