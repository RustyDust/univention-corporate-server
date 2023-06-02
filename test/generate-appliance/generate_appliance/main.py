#!/usr/bin/python3
# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

"""create virtual appliances for various virtualization systems from a single disk image"""

from __future__ import absolute_import, unicode_literals

import os
import re
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType, Namespace  # noqa: F401


try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore[assignment]

from logging import DEBUG, INFO, basicConfig
from tempfile import TemporaryDirectory

from .compat import BooleanOptionalAction
from .files import Lazy
from .files.raw import Raw


RE_INVALID = re.compile(r"""[][\t !"#$%&'()*./:;<=>?\\`{|}~]+-""")


def parse_options():
    # type: () -> Namespace
    parser = ArgumentParser(description=__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-d",
        "--verbose",
        action="count",
        help="Increase verbosity",
    )
    parser.add_argument(
        "-s",
        "--source",
        type=FileType("rb"),
        help="source image",
        required=True,
        metavar="PATH",
    )

    group = parser.add_argument_group("VM sizing")
    group.add_argument(
        "-m",
        "--memory-size",
        default=1024,
        type=int,
        help="size of virtual memory [MiB]",
        metavar="MiB",
    )
    group.add_argument(
        "-c",
        "--cpu-count",
        default=1,
        type=int,
        help="virtual CPU count",
        metavar="COUNT",
    )

    group = parser.add_argument_group("Output options")
    group.add_argument(
        "-f",
        "--filename",
        help="filename of appliance (default: derived from product)",
        metavar="PATH",
    )
    group.add_argument(
        "-n",
        "--no-target-specific-filename",
        action="store_true",
        help="do not append hypervisor target to filename of appliance. This is the default if only one target is chosen.",
    )

    group = parser.add_argument_group("Metadata settings")
    group.add_argument(
        "-p",
        "--product",
        help="product name of appliance",
        default="Univention Corporate Server (UCS)",
    )
    group.add_argument(
        "--product-url",
        help="product URL of appliance",
        default="https://www.univention.com/products/ucs/",
        metavar="URL",
    )
    group.add_argument(
        "-v",
        "--version",
        help="version string of appliance",
    )
    group.add_argument(
        "--vendor",
        help="vendor string of appliance",
        default="Univention GmbH",
    )
    group.add_argument(
        "--vendor-url",
        help="vendor URL of appliance",
        default="https://www.univention.com/",
        metavar="URL",
    )

    parser.add_argument(
        "-t",
        "--tempdir",
        help="temporary directory to use",
    )

    group = parser.add_argument_group("AWS settings")
    group.add_argument(
        "--region",
        help="EC2 region to use",
        default="eu-west-1",
    )
    group.add_argument(
        "--bucket",
        help="S3 bucket to use",
        default="generate-appliance",
    )

    group = parser.add_argument_group("Targets")
    group.add_argument(
        "-o",
        "--only",
        action="store_true",
        help="ignore default selections, only create selected targets",
    )

    eps = entry_points()
    targets = {ep.name: ep.load() for ep in eps.get("generate_appliance.targets", [])}
    for name, target in targets.items():
        group.add_argument(
            "--%s" % (name.replace("_", "-"),),
            help='create "%s"%s"' % (
                (target.__doc__ or "").strip(),
                ' (selected by default)' if target.default else '',
            ),
            action=BooleanOptionalAction,
        )

    options = parser.parse_args()

    options.choices = {
        target()
        for name, target in targets.items()
        if getattr(options, name) or target.default and not options.only
    }

    if len(options.choices) == 1:
        options.no_target_specific_filename = True

    if options.tempdir is not None:
        options.tempdir = os.path.realpath(options.tempdir)
        if not os.path.isdir(options.tempdir):
            parser.error('Tempdir %r is not a directory!')

    if options.filename is None:
        fn = "-".join(p for p in [options.product, options.version] if p)
        options.filename = RE_INVALID.sub('-', fn)

    return options


def setup_logging(level: int) -> None:
    basicConfig(level=DEBUG if level else INFO)


def main():
    # type: () -> None
    options = parse_options()
    setup_logging(options.verbose)
    with TemporaryDirectory(options.tempdir) as Lazy.BASEDIR:
        source_image = Raw(options.source)
        for choice in options.choices:
            choice.create(source_image, options)
