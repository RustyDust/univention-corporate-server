#!/usr/bin/python
"""Unit test for univention.config_registry.backend."""
# pylint: disable-msg=C0103,E0611,R0904

import os
import six
import time
from io import StringIO

import pytest

import univention.config_registry.backend as backend
from univention.config_registry.backend import ConfigRegistry

py2_only = pytest.mark.skipif(six.PY3, reason="Python 2 only")

TRUE_VALID = ('YES', 'yes', 'Yes', 'true', '1', 'enable', 'enabled', 'on')
TRUE_INVALID = ('yes ', ' yes', '')
FALSE_VALID = ('NO', 'no', 'No', 'false', '0', 'disable', 'disabled', 'off')
FALSE_INVALID = ('no ', ' no', '')


class TestConfigRegistry(object):

	"""
	Unit test for :py:class:`univention.config_registry.backend.ConfigRegistry`
	"""

	def test_normal(self, ucr0, tmpdir):
		"""Create default registry."""
		assert (tmpdir / ConfigRegistry.BASES[ConfigRegistry.NORMAL]).exists()

	@pytest.mark.parametrize("level", [
		ConfigRegistry.NORMAL,
		ConfigRegistry.LDAP,
		ConfigRegistry.SCHEDULE,
		ConfigRegistry.FORCED,
		ConfigRegistry.DEFAULTS,
	])
	def test_levels(self, level, ucr0, tmpdir):
		"""Create level registry."""
		_ucr = ConfigRegistry(write_registry=level)  # noqa F841
		assert (tmpdir / ConfigRegistry.BASES[level]).exists()

	def test_custom(self, ucr0, tmpdir):
		"""Create CUSTOM registry."""
		fname = tmpdir / 'custom.conf'

		_ucr = ConfigRegistry(str(fname))  # noqa F841

		assert fname.exists()

	def test_custom_through_env(self, monkeypatch, tmpdir):
		"""Create CUSTOM registry through environment variable."""
		fname = tmpdir / 'custom.conf'
		monkeypatch.setenv('UNIVENTION_BASECONF', str(fname))

		_ucr = ConfigRegistry()  # noqa F841

		assert fname.exists()

	def test_create_error(self, tmpdir):
		fname = tmpdir / "sub" / 'custom.conf'
		with pytest.raises(SystemExit):
			ConfigRegistry("/")

	def test_save_load(self, ucr0):
		"""Save and re-load UCR."""
		ucr0['foo'] = 'bar'
		ucr0.save()

		ucr = ConfigRegistry()
		ucr.load()
		assert ucr['foo'] == 'bar'

	def test_unset_getitem(self, ucr0):
		"""Test unset ucr[key]."""
		ucr = ConfigRegistry()
		assert ucr['foo'] is None

	def test_getitem(self, ucr0):
		"""Test set ucr[key]."""
		ucr0['foo'] = 'bar'
		assert ucr0['foo'] == 'bar'

	def test_empty_getitem(self, ucr0):
		"""Test empty ucr[key]."""
		ucr0['foo'] = ''
		assert ucr0['foo'] == ''

	def test_unset_get(self, ucr0):
		assert ucr0.get('foo') is None

	def test_get(self, ucr0):
		"""Test set ucr.get(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.get('foo') == 'bar'

	def test_empty_get(self, ucr0):
		"""Test empty ucr.get(key)."""
		ucr0['foo'] = ''
		assert ucr0.get('foo') == ''

	def test_default_get(self, ucr0):
		"""Test ucr.get(key, default)."""
		assert ucr0.get('foo', self) is self

	def test_scope_get_normal(self, ucr0):
		"""Test NORMAL ucr.get(key, default)."""
		ucr0['foo'] = 'bar'
		assert ucr0.get('foo', getscope=True) == (ConfigRegistry.NORMAL, 'bar')

	def test_scope_get_ldap(self, ucr0):
		"""Test LDAP ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.LDAP)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.LDAP, 'bar')

	def test_scope_get_schedule(self, ucr0):
		"""Test SCHEDULE ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.SCHEDULE)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.SCHEDULE, 'bar')

	def test_scope_get_forced(self, ucr0):
		"""Test FORCED ucr.get(key, default)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		assert ucr.get('foo', getscope=True) == (ConfigRegistry.FORCED, 'bar')

	def test_has_key_unset(self, ucr0):
		"""Test unset ucr.has_key(key)."""
		assert not ucr0.has_key('foo')  # noqa W601

	def test_has_key_set(self, ucr0):
		"""Test set ucr.has_key(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.has_key('foo')  # noqa W601

	def test_has_key_write_unset(self, ucr0):
		"""Test unset ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr['foo'] = 'bar'
		ucr = ConfigRegistry()
		assert not ucr.has_key('foo', write_registry_only=True)  # noqa W601

	def test_has_key_write_set(self, ucr0):
		"""Test set ucr.has_key(key, True)."""
		ucr = ConfigRegistry(write_registry=ConfigRegistry.FORCED)
		ucr = ConfigRegistry()
		ucr['foo'] = 'bar'
		assert ucr.has_key('foo', write_registry_only=True)  # noqa W601

	def test_pop(self, ucr0):
		"""Test set ucr.pop(key)."""
		ucr0['foo'] = 'bar'
		assert ucr0.pop('foo') == 'bar'

	def test_popitem(self, ucr0):
		"""Test set ucr.popitem()."""
		ucr0['foo'] = 'bar'
		assert ucr0.popitem() == ('foo', 'bar')

	def test_setdefault(self, ucr0):
		"""Test set ucr.setdefault()."""
		ucr0.setdefault('foo', 'bar')
		assert ucr0['foo'] == 'bar'

	def test_dict(self, ucrf):
		"""Test merged items."""
		assert dict(ucrf) == dict([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_items(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.items()) == sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_items_scopes(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.items(getscope=True)) == sorted([('foo', (ConfigRegistry.FORCED, 'FORCED')), ('bar', (ConfigRegistry.FORCED, 'FORCED')), ('baz', (ConfigRegistry.NORMAL, 'NORMAL'))])

	@py2_only
	def test_iteritems(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.iteritems()) == sorted([('foo', 'FORCED'), ('bar', 'FORCED'), ('baz', 'NORMAL')])

	def test_keys(self, ucrf):
		"""Test merged keys."""
		assert sorted(ucrf.keys()) == sorted(['foo', 'bar', 'baz'])

	@py2_only
	def test_iterkeys(self, ucrf):
		"""Test merged keys."""
		assert sorted(ucrf.iterkeys()) == sorted(['foo', 'bar', 'baz'])

	def test_values(self, ucrf):
		"""Test merged values."""
		assert sorted(ucrf.values()) == sorted(['FORCED', 'FORCED', 'NORMAL'])

	@py2_only
	def test_itervalues(self, ucrf):
		"""Test merged items."""
		assert sorted(ucrf.itervalues()) == sorted(['FORCED', 'FORCED', 'NORMAL'])

	def test_clear(self, ucrf):
		"""Test set ucr.clear()."""
		ucrf.clear()
		assert ucrf.get('foo', getscope=True) == (ConfigRegistry.FORCED, 'FORCED')
		assert ucrf.get('bar', getscope=True) == (ConfigRegistry.FORCED, 'FORCED')
		assert ucrf.get('baz', getscope=True) is None

	def test_is_true_unset(self, ucr0):
		"""Test unset is_true()."""
		assert not ucr0.is_true('foo')

	def test_is_true_default(self, ucr0):
		"""Test is_true(default)."""
		assert ucr0.is_true('foo', True)
		assert not ucr0.is_true('foo', False)

	@pytest.mark.parametrize("value", TRUE_VALID)
	def test_is_true_valid(self, value, ucr0):
		"""Test valid is_true()."""
		ucr0['foo'] = value
		assert ucr0.is_true('foo')

	@pytest.mark.parametrize("value", TRUE_INVALID)
	def test_is_true_invalid(self, value, ucr0):
		"""Test invalid is_true()."""
		ucr0['foo'] = value
		assert not ucr0.is_true('foo')

	@pytest.mark.parametrize("value", TRUE_VALID)
	def test_is_true_valid_direct(self, value, ucr0):
		"""Test valid is_true(value)."""
		assert ucr0.is_true(value=value)

	@pytest.mark.parametrize("value", TRUE_INVALID)
	def test_is_true_invalid_direct(self, value, ucr0):
		"""Test invalid is_true(value)."""
		assert not ucr0.is_true(value=value)

	def test_is_false_unset(self):
		"""Test unset is_false()."""
		ucr = ConfigRegistry()
		assert not ucr.is_false('foo')

	def test_is_false_default(self, ucr0):
		"""Test is_false(default)."""
		assert ucr0.is_false('foo', True)
		assert not ucr0.is_false('foo', False)

	@pytest.mark.parametrize("value", FALSE_VALID)
	def test_is_false_valid(self, value, ucr0):
		"""Test valid is_false()."""
		ucr0['foo'] = value
		assert ucr0.is_false('foo')

	@pytest.mark.parametrize("value", FALSE_INVALID)
	def test_is_false_invalid(self, value, ucr0):
		"""Test invalid is_false()."""
		ucr0['foo'] = value
		assert not ucr0.is_false('foo')

	@pytest.mark.parametrize("value", FALSE_VALID)
	def test_is_false_valid_direct(self, value, ucr0):
		"""Test valid is_false(value)."""
		assert ucr0.is_false(value=value)

	@pytest.mark.parametrize("value", FALSE_INVALID)
	def test_is_false_invalid_direct(self, value, ucr0):
		"""Test valid is_false(value)."""
		assert not ucr0.is_false(value=value)

	def test_update(self, ucr0):
		"""Test update()."""
		ucr0['foo'] = 'foo'
		ucr0['bar'] = 'bar'
		assert ucr0.update({
			'foo': None,
			'bar': 'baz',
			'baz': 'bar',
			'bam': None,
		}) == {
			"foo": ("foo", None),
			"bar": ("bar", "baz"),
			"baz": (None, "bar"),
		}
		assert ucr0.get('foo') is None
		assert ucr0.get('bar') == 'baz'
		assert ucr0.get('baz') == 'bar'
		assert ucr0.get('bam') is None

	def test_locking(self, ucr0):
		"""Test inter-process-locking."""
		delay = 1.0
		read_end, write_end = os.pipe()

		pid1 = os.fork()
		if not pid1:  # child 1
			os.close(read_end)
			ucr0.lock()
			os.write(write_end, b'1')
			time.sleep(delay)
			ucr0.unlock()
			os._exit(0)

		pid2 = os.fork()
		if not pid2:  # child 2
			os.close(write_end)
			os.read(read_end, 1)
			ucr0.lock()
			time.sleep(delay)
			ucr0.unlock()
			os._exit(0)

		os.close(read_end)
		os.close(write_end)

		timeout = time.time() + delay * 3
		while time.time() < timeout:
			pid, status = os.waitpid(0, os.WNOHANG)
			if (pid, status) == (0, 0):
				time.sleep(0.1)
			elif pid == pid1:
				assert os.WIFEXITED(status) is True
				assert os.WEXITSTATUS(status) == 0
				pid1 = None
			elif pid == pid2:
				assert os.WIFEXITED(status) is True
				assert os.WEXITSTATUS(status) == 0
				assert pid1 is None, 'child 2 exited before child 1'
				break
			else:
				self.fail('Unknown child status: %d, %x' % (pid, status))
		else:
			self.fail('Timeout')

	def test_context(self, ucr0):
		with ucr0:
			ucr0["foo"] = "bar"

		ucr = ConfigRegistry()
		ucr.load()
		assert ucr['foo'] == 'bar'

	def test_context_error(self, ucr0):
		ex = ValueError()
		with pytest.raises(ValueError) as exc_info, ucr0:
			ucr0["foo"] = "bar"
			raise ex

		assert exc_info.value is ex
		ucr = ConfigRegistry()
		ucr.load()
		assert ucr['foo'] is None

	def test_exception(self):
		io = StringIO()
		with pytest.raises(SystemExit) as exc_info:
			backend.exception_occured(io)

		assert exc_info.value.code != 0
		assert io.getvalue() > ""

	def test_str(self, ucr0):
		ucr0["foo"] = "bar"
		assert str(ucr0) == "foo: bar"


class TestInternal(object):

	"""
	Unit test for py:class:`univention.config_registry.backend._ConfigRegistry`
	"""

	def test_load_backup(self, tmpdir):
		tmp = tmpdir / "test.conf"
		tmp.write("")
		bak = tmpdir / "test.conf.bak"
		bak.write("#\nfoo: bar")

		ucr = backend._ConfigRegistry(str(tmp))
		ucr.load()
		assert ucr["foo"] == "bar"
		assert tmp.size() > 0

	def test_busy(self, tmpdir):
		tmp = tmpdir / "test.conf"
		tmpdir.mkdir("test.conf.temp")

		ucr = backend._ConfigRegistry(str(tmp))
		with pytest.raises(EnvironmentError) as exc_info:
			ucr._save_file(str(tmp))

	@pytest.mark.parametrize("text,data", [
		("", {}),
		("\n", {}),
		("foo # bar", {}),
		("bar", {}),
		("a:b", {}),
		("key: #value", {"key": "#value"}),
		("key:  # value ", {"key": "# value"}),
	])
	def test_load_unusual(self, text, data, tmpdir):
		tmp = tmpdir / "test.conf"
		tmp.write("# univention_ base.conf\n" + text)

		ucr = backend._ConfigRegistry(str(tmp))
		ucr.load()
		assert ucr.items() == data.items()

	@py2_only
	def test_strict_key(self):
		ucr = backend._ConfigRegistry(os.path.devnull)
		ucr.strict_encoding = True
		with pytest.raises(backend.StrictModeException):
			ucr[b'\xff'] = "val"

	@py2_only
	def test_strict_value(self):
		ucr = backend._ConfigRegistry(os.path.devnull)
		ucr.strict_encoding = True
		with pytest.raises(backend.StrictModeException):
			ucr["key"] = b"\xff"


class TestDefault(object):
	def test_default(self, ucr0, tmpdir):
		ucr0._registry[ucr0.DEFAULTS]["key"] = "val"
		assert ucr0["key"] == "val"
		assert ucr0.items() == {"key": "val"}.items()

	def test_subst(self, ucr0, tmpdir):
		ucr0["ref"] = "val"
		ucr0._registry[ucr0.DEFAULTS]["key"] = "@%@ref@%@"
		assert ucr0["key"] == "val"

	@pytest.mark.timeout(timeout=3)
	def test_recusrion(self, ucr0, tmpdir):
		ucr0._registry[ucr0.DEFAULTS]["key"] = "@%@key@%@"
		assert ucr0["key"] == ""
