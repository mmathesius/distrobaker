# SPDX-License-Identifier: MIT

import distrobaker
import importlib
import logging
import os
import subprocess
import sys
import tempfile

from io import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


GIT_HASH_REGEX = r"^[0-9a-f]{5,40}$"


def _import_path(path):
    """Imports python script as a module

    :param path: Path to python script to import
    :returns: imported module object
    """
    module_name = os.path.basename(path).replace("-", "_")
    spec = importlib.util.spec_from_loader(
        module_name, importlib.machinery.SourceFileLoader(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # sys.modules[module_name] = module
    return module


def _last_commit(repodir):
    cmd = ["git", "rev-parse", "--verify", "HEAD"]
    proc = subprocess.Popen(
        cmd, cwd=repodir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    return out.rstrip()


def _run_cmds(cmds):
    cwd = None
    for cmd in cmds:
        if cmd[0] == "cd":
            cwd = cmd[1]
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = proc.communicate()


class TestConfigRef(unittest.TestCase):
    def setUp(self):
        # configure logging
        logging.basicConfig(format="%(asctime)s : %(levelname)s : %(message)s")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("logging has been configured")

        # import main distrobaker script as a module
        self.dbmain = _import_path("distrobaker")

        # create a temporary directoy to use as a git repo
        self.git_repo_dirobj = tempfile.TemporaryDirectory()
        self.git_repo_dir = self.git_repo_dirobj.name
        self.logger.debug("git repo dir = %s" % self.git_repo_dir)

    def tearDown(self):
        self.git_repo_dirobj.cleanup()
        pass

    def _setup_repo(self):
        clone_dirobj = tempfile.TemporaryDirectory()
        clone_dir = clone_dirobj.name

        # setup a simple bare repo containing a README and a config file
        cmds = (
            ["cd", "/tmp"],
            ["git", "init", "--bare", self.git_repo_dir],
            ["rm", "-rf", clone_dir],
            ["git", "clone", self.git_repo_dir, clone_dir],
            ["cd", clone_dir],
            ["git", "config", "user.name", "John Doe"],
            ["git", "config", "user.email", "jdoe@example.com"],
            ["bash", "-c", "echo test > README"],
            ["touch", "distrobaker.yaml"],
            ["git", "add", "."],
            ["git", "commit", "-m", "Initial commit"],
            ["git", "push"],
            ["cd", self.git_repo_dir],
            ["git", "branch", "-m", "main"],
        )
        _run_cmds(cmds)

    def test_get_config_ref(self):
        self._setup_repo()

        last_commit = _last_commit(self.git_repo_dir)
        self.logger.debug("git last commit = %s" % last_commit)
        self.assertRegex(last_commit.decode(), GIT_HASH_REGEX)

        config_ref = self.dbmain.get_config_ref(
            self.git_repo_dir + "#main", self.logger
        )
        self.logger.debug("config ref = %s" % config_ref)
        self.assertRegex(config_ref.decode(), GIT_HASH_REGEX)

        self.assertEqual(config_ref, last_commit)

        config_ref = self.dbmain.get_config_ref(
            self.git_repo_dir + "#doesnotexist", self.logger
        )
        self.logger.debug("config ref = %s" % config_ref)
        self.assertEqual(config_ref, None)


class TestConsole(unittest.TestCase):
    def setUp(self):
        # import main distrobaker script as a module
        self.dbmain = _import_path("distrobaker")

    @patch("sys.stdout", new=StringIO())
    @patch("sys.argv", ["distrobaker", "-h"])
    def test_main_help(self):
        with self.assertRaises(SystemExit) as cm:
            self.dbmain.main()
        self.assertEqual(cm.exception.code, 0)
        output = sys.stdout.getvalue()
        self.assertIn("show this help message and exit", output)
