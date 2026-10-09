# Copyright 2026 Canonical Ltd.
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

"""Tests for the snap configuration model."""

import unittest

import pydantic

from manila_data import configuration as config


class TestSettings(unittest.TestCase):
    """Tests the settings configuration."""

    def _ips(self, value):
        options = {"data-node-access-ips": value}
        return config.Settings.model_validate(options).data_node_access_ips

    def test_data_node_access_ips_default(self):
        """Tests data_node_access_ips is unset by default."""
        self.assertIsNone(config.Settings().data_node_access_ips)
        self.assertIsNone(self._ips(None))

    def test_data_node_access_ips_normalized(self):
        """Tests IPs are stripped and joined without spaces."""
        self.assertEqual(self._ips("10.0.0.5"), "10.0.0.5")
        value = " 10.0.0.5 ,2001:db8::5, "
        self.assertEqual(self._ips(value), "10.0.0.5,2001:db8::5")

    def test_data_node_access_ips_empty(self):
        """Tests an empty or blank list is treated as unset."""
        self.assertIsNone(self._ips(""))
        self.assertIsNone(self._ips(" "))
        self.assertIsNone(self._ips(" , "))

    def test_data_node_access_ips_invalid(self):
        """Tests invalid addresses are rejected."""
        for value in ("foo", "10.0.0.5,foo", "10.0.0.256", "10.0.0.0/24"):
            with self.subTest(value=value):
                with self.assertRaises(pydantic.ValidationError):
                    self._ips(value)
