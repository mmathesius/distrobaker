# SPDX-License-Identifier: MIT

import distrobaker
import logging
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "config")


class TestConfigSetting(unittest.TestCase):
    def test_initial_config(self):
        # configuration should start out empty
        cfg = distrobaker.get_config()
        self.assertIs(type(cfg), dict)
        self.assertFalse(cfg)

    def test_load_config(self):
        # FIXME: create test repo with config from DATA_DIR, load config, verify loaded values
        pass
