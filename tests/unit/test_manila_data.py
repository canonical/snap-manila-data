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
import shutil
import tempfile
import unittest
from unittest import mock

import snaphelpers

from manila_data import configuration as config
from manila_data import manila_data


class TestManilaDataService(unittest.TestCase):
    """Tests manila_data."""

    def setUp(self):
        """Test setup."""
        tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp_dir)

        self.tmpdir = pathlib.Path(tmp_dir)
        self.snap = mock.Mock()
        env = {
            "COMMON": self.tmpdir / "common",
            "DATA": self.tmpdir / "data",
            "REAL_HOME": self.tmpdir / "home",
            "SNAP": self.tmpdir / "snap",
            "USER_COMMON": self.tmpdir / "user_common",
            "USER_DATA": self.tmpdir / "user_data",
        }
        self.snap.paths = snaphelpers.SnapPaths(env)

        self.snap.config.get_options.return_value.as_dict.return_value = {
            "database": config.DatabaseConfiguration(url="foo"),
            "rabbitmq": config.RabbitMQConfiguration(url="lish"),
            "settings": config.Settings(),
        }

        self.manila_service = mock.Mock()
        self.snap.services.list.return_value = {
            "manila-data": self.manila_service,
        }

    def _check_file_contents(self, path, strings):
        with open(path) as f:
            data = f.read()

        for string in strings:
            self.assertIn(string, data)

    @mock.patch("manila_data.log.setup_logging", mock.Mock())
    def test_install_hook(self):
        """Tests the install hook."""
        manila_data.GenericManilaData.install_hook(self.snap)

        tmp = str(self.tmpdir)
        manila_conf_path = str(self.tmpdir / "common/etc/manila/manila.conf")
        rootwrap_path = str(self.tmpdir / "common/etc/manila/rootwrap.conf")
        expected_manila_conf = [
            f"rootwrap_config = {rootwrap_path}",
            "debug = False",
            f"state_path = {tmp}/common/lib/manila",
            "transport_url = lish",
            "connection = foo",
            f"lock_path = {tmp}/common/lib/manila/tmp",
        ]
        self._check_file_contents(manila_conf_path, expected_manila_conf)

        expected_rootwrap = [
            (
                f"filters_path={tmp}/common/etc/manila/rootwrap.d,"
                f"{tmp}/snap/usr/share/manila/rootwrap"
            ),
            (
                f"exec_dirs={tmp}/snap/sbin,{tmp}/snap/usr/sbin,"
                f"{tmp}/snap/bin,{tmp}/snap/usr/bin,{tmp}/snap/usr/local/bin,"
                f"{tmp}/snap/usr/local/sbin,{tmp}/snap/usr/lpp/mmfs/bin"
            ),
        ]
        self._check_file_contents(rootwrap_path, expected_rootwrap)

    @mock.patch("manila_data.log.setup_logging", mock.Mock())
    def test_configure_hook(self):
        """Tests the configure hook."""
        manila_data.GenericManilaData.configure_hook(self.snap)

        manila_conf_path = str(self.tmpdir / "common/etc/manila/manila.conf")
        expected_manila_conf = [
            "transport_url = lish",
            "connection = foo",
        ]
        self._check_file_contents(manila_conf_path, expected_manila_conf)

        self.manila_service.restart.assert_called_once()
