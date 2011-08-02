# -*- coding: utf-8 -*-
#
# Univention Admin Modules
#  password encryption methods
#
# Copyright 2004-2011 Univention GmbH
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

import os, heimdal, codecs, types, string, sys
import smbpasswd

def crypt(password):
	"""return crypt hash"""

	valid = ['.', '/', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
		'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
		'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
		'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
		'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5',
		'6', '7', '8', '9' ]
	salt = ''
	urandom = open("/dev/urandom", "r")
	for i in range(0,8):
		o = urandom.read(1)
		salt = salt + valid[(ord(o) % 64)]

	urandom.close()

	import crypt
	return crypt.crypt(password.encode('utf-8'), '$1$%s$' % salt)

def ntlm(password):
	"""return tuple with NT and LanMan hash"""

	(lm, nt) = smbpasswd.hash(password)

	return (nt, lm)

def krb5_asn1(principal, password, krb5_context=None):
	list=[]
	if type(principal) == types.UnicodeType:
		principal = str( principal )
	if type(password) == types.UnicodeType:
		password = str( password )
	if not krb5_context:
		krb5_context = heimdal.context()
	for krb5_etype in krb5_context.get_permitted_enctypes():
		krb5_principal = heimdal.principal(krb5_context, principal)
		krb5_keyblock = heimdal.keyblock(krb5_context, krb5_etype, password, krb5_principal)
		krb5_salt = heimdal.salt(krb5_context, krb5_principal)
		list.append(heimdal.asn1_encode_key(krb5_keyblock, krb5_salt, 0))
	return list
