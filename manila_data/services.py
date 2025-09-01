# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import logging
import subprocess
import sys
import typing
from pathlib import Path

from snaphelpers import Snap

from . import log

_SERVICES: list[typing.Type["OpenStackService"]] = []


def entry_point(service_class):
    """Entry point wrapper for services."""
    service = service_class()
    exit_code = service.run(Snap())
    sys.exit(exit_code)


def services() -> typing.Sequence[typing.Type["OpenStackService"]]:
    return _SERVICES


class OpenStackService:
    """Base service object for OpenStack daemons."""

    # only fully specified configuration files will trigger a restart
    # on modification
    configuration_files: typing.Sequence[Path] = []

    name: str
    executable: Path

    def __init_subclass__(cls, **kwargs):
        """Register inherited classes."""
        super().__init_subclass__(**kwargs)
        _SERVICES.append(cls)

    def run(self, snap: Snap) -> int:
        """Runs the OpenStack service.

        Invoked when this service is started.

        :param snap: the snap context
        :type snap: Snap
        :return: exit code of the process
        :rtype: int
        """
        log.setup_logging(snap.paths.common / f"{self.executable.name}-{snap.name}.log")

        args = []
        for conf_file in self.configuration_files:
            args.extend(
                [
                    "--config-file",
                    str(snap.paths.common / conf_file),
                ]
            )

        executable = snap.paths.snap / self.executable

        cmd = [str(executable)]
        cmd.extend(args)
        completed_process = subprocess.run(cmd)

        logging.info(f"Exiting with code {completed_process.returncode}")
        return completed_process.returncode


class ManilaDataService(OpenStackService):
    configuration_files = [
        Path("etc/manila/manila.conf"),
        Path("etc/manila/rootwrap.conf"),
    ]
    name = "manila-data"
    executable = Path("usr/bin/manila-data")


manila_data = functools.partial(entry_point, ManilaDataService)
