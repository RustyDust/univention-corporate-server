"""Import all UCS Test formatters."""
from univention.testing.format.html import HTML as format_html  # noqa: F401
from univention.testing.format.jenkins import Jenkins as format_jenkins  # noqa: F401
from univention.testing.format.junit import Junit as format_junit  # noqa: F401
from univention.testing.format.tap import TAP as format_tap  # noqa: F401
from univention.testing.format.text import Raw as format_raw, Text as format_text  # noqa: F401


FORMATS = [f[7:] for f in dir() if f.startswith('format_')]
