# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for ManilaDataService."""

import pathlib
import unittest
from unittest import mock

from manila_data import services


class TestManilaDataService(unittest.TestCase):
    """manila_data.services tests."""

    @mock.patch("sys.exit")
    @mock.patch("manila_data.log.setup_logging", mock.Mock())
    @mock.patch("subprocess.run")
    @mock.patch.object(services, "Snap")
    def test_service_run(self, mock_snap, mock_run, mock_exit):
        """Tests OpenStackService run."""
        snap = mock_snap.return_value
        snap.paths.common = pathlib.Path("/foo")
        snap.paths.snap = pathlib.Path("/lish")

        services.manila_data()

        mock_run.assert_called_once_with(
            [
                "/lish/usr/bin/manila-data",
                "--config-file",
                "/foo/etc/manila/manila.conf",
                "--config-file",
                "/foo/etc/manila/rootwrap.conf",
            ]
        )
        mock_exit.assert_called_once_with(mock_run.return_value.returncode)
