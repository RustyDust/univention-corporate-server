#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-
#
#
import os, sys, imp, optparse
try:
	import univention.ucslint.base as uub
except ImportError:
	print >> sys.stderr, 'using fallback ucslint.base instead of univention.ucslint.base'
	import ucslint.base as uub


class DebianPackageCheck(object):
	def __init__(self, path, plugindirs, enabled_modules=None, disabled_modules=None, debuglevel=0):
		self.path = path
		self.plugindirs = plugindirs
		self.pluginlist = {}
		self.msglist = []
		self.enabled_modules = enabled_modules
		self.disabled_modules = disabled_modules
		self.debuglevel = debuglevel
		self.msgidlist = {}
		self.loadplugins()


	def loadplugins(self):
		for plugindir in plugindirs:
			plugindir = os.path.expanduser(plugindir)
			if not os.path.exists(plugindir):
				if self.debuglevel:
					print 'WARNING: plugindir %s does not exist' % plugindir
			else:
				for f in os.listdir( plugindir ):
					if f.endswith('.py') and f[0:4].isdigit():
						# self.modules == None ==> load all modules
						# otherwise load only listed modules
						if ( not self.enabled_modules or f[0:4] in self.enabled_modules ) and not f[0:4] in self.disabled_modules:
							modname = f[0:-3]
							fd = open( os.path.join( plugindir, f ) )
							module = imp.new_module(modname)
							try:
								exec fd in module.__dict__
								self.pluginlist[modname] = module
								if self.debuglevel:
									print 'Loaded module %s' % modname
							except:
								print 'ERROR: Loading module %s failed' % f
								if self.debuglevel:
									raise
						else:
							if self.debuglevel:
								print 'Module %s is not enabled' % f


	def check(self):
		for plugin in self.pluginlist.values():
			obj = plugin.UniventionPackageCheck()
			self.msgidlist.update( obj.getMsgIds() )
			obj.setdebug( self.debuglevel )
			obj.postinit( self.path )
			obj.check( self.path )
			self.msglist.extend( obj.result() )


	def modifyMsgIdList(self, newmap):
		""" newmap == { RESULT_WARN: [ '0004-1', '0019-17', ... ],
						RESULT_ERROR: [ '0004-2' ],
						}
		"""
		for level, idlist in newmap.items():
			for curid in idlist:
				if curid in self.msgidlist:
					self.msgidlist[ curid ][0] = level


	def printResult(self, ignore_IDs, display_only_IDs, display_only_categories, exitcode_categories ):
		incident_cnt = 0
		exitcode_cnt = 0
		for msg in self.msglist:
			if msg.getId() in ignore_IDs:
				continue
			if display_only_IDs and not msg.getId() in display_only_IDs:
				continue
			category = uub.RESULT_INT2STR.get( self.msgidlist.get( msg.getId(), ['FIXME'] )[0], 'FIXME')
			if category in display_only_categories or display_only_categories == '':
				print '%s:%s' % (category , str(msg))
				incident_cnt += 1

				if category in exitcode_categories or exitcode_categories == '':
					exitcode_cnt += 1

		return incident_cnt, exitcode_cnt

def clean_id(idstr):
	if not '-' in idstr:
		raise Exception('no valid id (%s) - missing dash' % idstr)
	modid, msgid = idstr.strip().split('-',1)
	return '%s-%s' % (clean_modid(modid), clean_msgid(msgid))

def clean_modid(modid):
	if not modid.isdigit():
		raise Exception('modid contains invalid characters: %s' % modid)
	return '%s%s' % ((4-len(modid.strip())) * '0', modid)

def clean_msgid(msgid):
	if not msgid.isdigit():
		raise Exception('msgid contains invalid characters: %s' % msgid)
	return '%d' % int(msgid)


def usage():
	print 'ucslint [-d] [<path>]'

if __name__ == '__main__':
	parser = optparse.OptionParser()
	parser.add_option( '-d', '--debug', action = 'store', type = 'int',
					   dest = 'debug', default = 0,
					   help = 'if set, debugging is activated and set to the specified level' )

	parser.add_option( '-m', '--modules', action = 'store', type = 'string',
					   dest = 'enabled_modules', default = '',
					   help = 'list of modules to be loaded (e.g. -m 0009,27)' )

	parser.add_option( '-x', '--exclude-modules', action = 'store', type = 'string',
					   dest = 'disabled_modules', default = '',
					   help = 'list of modules to be disabled (e.g. -x 9,027)' )

	parser.add_option( '-o', '--display-only', action = 'store', type = 'string',
					   dest = 'display_only_IDs', default = '',
					   help = 'list of IDs to be displayed (e.g. -o 9-1,0027-12)' )

	parser.add_option( '-i', '--ignore', action = 'store', type = 'string',
					   dest = 'ignore_IDs', default = '',
					   help = 'list of IDs to be ignored (e.g. -i 0003-4,19-27)' )

	parser.add_option( '-p', '--plugindir', action = 'store', type = 'string',
					   dest = 'plugindir', default = '',
					   help = 'override plugin directory with <plugindir>' )

	parser.add_option( '-c', '--display-categories', action = 'store', type = 'string',
					   dest = 'display_only_categories', default = '',
					   help = 'categories to be displayed (e.g. -c EWIS)' )

	parser.add_option( '-e', '--exitcode-categories', action = 'store', type = 'string',
					   dest = 'exitcode_categories', default = 'E',
					   help = 'categories that cause an exitcode != 0 (e.g. -e EWIS)' )

	( options, args ) = parser.parse_args()

	pkgpath = '.'
	if len(args) > 0:
		pkgpath = args[0]

	if not os.path.exists( pkgpath ):
		print "ERROR: directory %s does not exist!" % pkgpath
		sys.exit(1)

	if not os.path.isdir( pkgpath ):
		print "ERROR: %s is no directory!" % pkgpath
		sys.exit(1)

	if not os.path.isdir( os.path.join(pkgpath, 'debian') ):
		print "ERROR: %s/debian does not exist or is not a directory!" % pkgpath
		sys.exit(1)

	plugindirs = [ '~/.ucslint', '/usr/lib/python2.4/site-packages/univention/ucslint' ]

	# override plugin directories
	if options.plugindir:
		plugindirs = [ options.plugindir ]

	if options.ignore_IDs:
		options.ignore_IDs = options.ignore_IDs.split(',')
		options.ignore_IDs = [ clean_id(x) for x in options.ignore_IDs ]

	if options.display_only_IDs:
		options.display_only_IDs = options.display_only_IDs.split(',')
		options.display_only_IDs = [ clean_id(x) for x in options.display_only_IDs ]

	if options.enabled_modules:
		options.enabled_modules = options.enabled_modules.split(',')
		options.enabled_modules = [ clean_modid(x) for x in options.enabled_modules ]
	else:
		options.enabled_modules = []

	if options.disabled_modules:
		options.disabled_modules = options.disabled_modules.split(',')
		options.disabled_modules = [ clean_modid(x) for x in options.disabled_modules ]
	else:
		options.disabled_modules = []

	chk = DebianPackageCheck( pkgpath, plugindirs, enabled_modules=options.enabled_modules, disabled_modules=options.disabled_modules, debuglevel=options.debug )
	chk.check()
	incident_cnt, exitcode_cnt = chk.printResult( options.ignore_IDs, options.display_only_IDs, options.display_only_categories, options.exitcode_categories )

	if exitcode_cnt:
		sys.exit(1)
	sys.exit(0)

