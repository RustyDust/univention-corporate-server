#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.modules as umcm

from .ldap import UDM_Module, UDM_Settings, ldap_dn2path

_ = umc.Translation( 'univention-management-console-modules-udm' ).translate

class Instance( umcm.Base ):
	def __init__( self ):
		umcm.Base.__init__( self )
		self.settings = None

	def init( self ):
		'''Initialize the module. Invoked when ACLs, commands and
		credentials are available'''
		self.settings = UDM_Settings( self._username )

	def put( self, request ):
		self.finished( request.id )

	def remove( self, request ):

		self.finished( request.id )

	def get( self, request ):

		self.finished( request.id )

	def query( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( module_name )

		result = module.search( request.options[ 'container' ], request.options[ 'objectProperty' ], request.options[ 'objectPropertyValue' ] )

		self.finished( request.id, map( lambda obj: { 'ldap-dn' : obj.dn, 'name' : obj[ module.identifies ], 'path' : ldap_dn2path( obj.dn ) }, result ) )

	def values( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name or 'all' == module_name:
			module_name = request.flavor
		property_name = request.options.get( 'objectProperty' )
		module = UDM_Module( module_name )

		self.finished( request.id, module.get_default_values( property_name ) )

	def containers( self, request ):
		self.finished( request.id, self.settings.containers( request.flavor ) )

	def types( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.child_modules )

	def layout( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.layout )

	def properties( self, request ):
		module_name = request.options.get( 'objectType' )
		if not module_name:
			module_name = request.flavor
		module = UDM_Module( request.flavor )
		properties = module.properties
		if request.options.get( 'searchable', False ):
			properties = filter( lambda prop: prop[ 'searchable' ], properties )
		self.finished( request.id, properties )

	def options( self, request ):
		module = UDM_Module( request.flavor )
		self.finished( request.id, module.options )
