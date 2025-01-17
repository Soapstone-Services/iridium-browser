#!/usr/bin/env python3
# Copyright (c) 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import hashlib
import os
import os.path
import sys
import time
import unittest
import unittest.mock

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import gclient_paths
import ninja_reclient
import reclient_helper
from testing_support import trial_dir


def write(filename, content):
    """Writes the content of a file and create the directories as needed."""
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as f:
        f.write(content)


class NinjaReclientTest(trial_dir.TestCase):
    def setUp(self):
        super(NinjaReclientTest, self).setUp()
        self.previous_dir = os.getcwd()
        os.chdir(self.root_dir)

    def tearDown(self):
        os.chdir(self.previous_dir)
        super(NinjaReclientTest, self).tearDown()

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('reclient_helper.datetime_now',
                         return_value=datetime.datetime(2017, 3, 16, 20, 0, 41,
                                                        0))
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=False)
    def test_ninja_reclient_sets_path_env_vars(self, *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        run_log_dir = os.path.join(self.root_dir, "out", "a", ".reproxy_tmp",
                                   "logs",
                                   "20170316T200041.000000_SOME_RANDOM_ID")

        self.assertTrue(
            os.path.isdir(
                os.path.join(self.root_dir, "out", "a", ".reproxy_tmp")))
        self.assertTrue(
            os.path.isdir(
                os.path.join(
                    self.root_dir, ".reproxy_cache",
                    hashlib.md5(
                        os.path.join(self.root_dir, "out", "a",
                                     ".reproxy_tmp").encode()).hexdigest())))
        self.assertTrue(os.path.isdir(run_log_dir))
        self.assertEqual(os.environ.get('RBE_output_dir'), run_log_dir)
        self.assertEqual(os.environ.get('RBE_proxy_log_dir'), run_log_dir)
        self.assertEqual(
            os.environ.get('RBE_cache_dir'),
            os.path.join(
                self.root_dir, ".reproxy_cache",
                hashlib.md5(
                    os.path.join(self.root_dir, "out", "a",
                                 ".reproxy_tmp").encode()).hexdigest()))
        if sys.platform.startswith('win'):
            self.assertEqual(
                os.environ.get('RBE_server_address'),
                "pipe://%s/reproxy.pipe" % hashlib.md5(
                    os.path.join(self.root_dir, "out", "a",
                                 ".reproxy_tmp").encode()).hexdigest())
        else:
            self.assertEqual(
                os.environ.get('RBE_server_address'),
                "unix:///tmp/reproxy_%s.sock" % hashlib.sha256(
                    os.path.join(self.root_dir, "out", "a",
                                 ".reproxy_tmp").encode()).hexdigest())

    @unittest.mock.patch.dict(os.environ, {})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=False)
    def test_ninja_reclient_calls_reclient_binaries(self, mock_metrics_status,
                                                    mock_ninja, mock_call):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        mock_metrics_status.assert_called_once_with("out/a")
        mock_ninja.assert_called_once_with(argv)
        mock_call.assert_has_calls([
            unittest.mock.call([
                os.path.join(self.root_dir, reclient_bin_dir,
                             'bootstrap' + gclient_paths.GetExeSuffix()),
                "--re_proxy=" +
                os.path.join(self.root_dir, reclient_bin_dir,
                             'reproxy' + gclient_paths.GetExeSuffix()),
                "--cfg=" + os.path.join(self.root_dir, reclient_cfg)
            ]),
            unittest.mock.call([
                os.path.join(self.root_dir, reclient_bin_dir,
                             'bootstrap' + gclient_paths.GetExeSuffix()),
                "--shutdown",
                "--cfg=" + os.path.join(self.root_dir, reclient_cfg)
            ]),
        ])

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=True)
    def test_ninja_reclient_collect_metrics_cache_missing(
            self, mock_metrics_status, *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        self.assertIn("/SOME_RANDOM_ID", os.environ["RBE_invocation_id"])
        self.assertEqual(os.environ.get('RBE_metrics_project'),
                         "chromium-reclient-metrics")
        self.assertEqual(os.environ.get('RBE_metrics_table'),
                         "rbe_metrics.builds")
        self.assertEqual(
            os.environ.get('RBE_metrics_labels'),
            "source=developer,tool=ninja_reclient,"
            "creds_cache_status=missing,creds_cache_mechanism=UNSPECIFIED")
        self.assertEqual(os.environ.get('RBE_metrics_prefix'),
                         "go.chromium.org")

        mock_metrics_status.assert_called_once_with("out/a")

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('reclient_helper.datetime_now',
                         return_value=datetime.datetime(2017, 3, 16, 20, 0, 41,
                                                        0))
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=True)
    def test_ninja_reclient_collect_metrics_cache_valid(self,
                                                        mock_metrics_status,
                                                        *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        cache_dir = os.path.join(
            self.root_dir, ".reproxy_cache",
            hashlib.md5(
                os.path.join(self.root_dir, "out", "a",
                             ".reproxy_tmp").encode()).hexdigest())
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        write(
            os.path.join(cache_dir, "reproxy.creds"), """
mechanism:  GCLOUD
expiry:  {
  seconds:  %d
}
              """ % (int(time.time()) + 10 * 60))
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        self.assertIn("/SOME_RANDOM_ID", os.environ["RBE_invocation_id"])
        self.assertEqual(os.environ.get('RBE_metrics_project'),
                         "chromium-reclient-metrics")
        self.assertEqual(os.environ.get('RBE_metrics_table'),
                         "rbe_metrics.builds")
        self.assertEqual(
            os.environ.get('RBE_metrics_labels'),
            "source=developer,tool=ninja_reclient,"
            "creds_cache_status=valid,creds_cache_mechanism=GCLOUD")
        self.assertEqual(os.environ.get('RBE_metrics_prefix'),
                         "go.chromium.org")

        mock_metrics_status.assert_called_once_with("out/a")

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=True)
    def test_ninja_reclient_collect_metrics_cache_expired(
            self, mock_metrics_status, *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        cache_dir = os.path.join(
            self.root_dir, ".reproxy_cache",
            hashlib.md5(
                os.path.join(self.root_dir, "out", "a",
                             ".reproxy_tmp").encode()).hexdigest())
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        write(
            os.path.join(cache_dir, "reproxy.creds"), """
mechanism:  GCLOUD
expiry:  {
  seconds:  %d
}
              """ % (int(time.time())))
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        self.assertIn("/SOME_RANDOM_ID", os.environ["RBE_invocation_id"])
        self.assertEqual(os.environ.get('RBE_metrics_project'),
                         "chromium-reclient-metrics")
        self.assertEqual(os.environ.get('RBE_metrics_table'),
                         "rbe_metrics.builds")
        self.assertEqual(
            os.environ.get('RBE_metrics_labels'),
            "source=developer,tool=ninja_reclient,"
            "creds_cache_status=expired,creds_cache_mechanism=GCLOUD")
        self.assertEqual(os.environ.get('RBE_metrics_prefix'),
                         "go.chromium.org")

        mock_metrics_status.assert_called_once_with("out/a")

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=False)
    def test_ninja_reclient_do_not_collect_metrics(self, mock_metrics_status,
                                                   *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(0, ninja_reclient.main(argv))

        self.assertEqual(os.environ.get('RBE_metrics_project'), None)
        self.assertEqual(os.environ.get('RBE_metrics_table'), None)
        self.assertEqual(os.environ.get('RBE_metrics_labels'), None)
        self.assertEqual(os.environ.get('RBE_metrics_prefix'), None)

        mock_metrics_status.assert_called_once_with("out/a")

    @unittest.mock.patch.dict(os.environ,
                              {'AUTONINJA_BUILD_ID': "SOME_RANDOM_ID"})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    @unittest.mock.patch('reclient_metrics.check_status', return_value=True)
    @unittest.mock.patch('reclient_helper.datetime_now')
    def test_ninja_reclient_clears_log_dir(self, mock_now, *_):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        for i in range(7):
            os.environ["AUTONINJA_BUILD_ID"] = "SOME_RANDOM_ID_%d" % i
            run_time = datetime.datetime(2017, 3, 16, 20, 0, 40 + i, 0)
            mock_now.return_value = run_time
            self.assertEqual(0, ninja_reclient.main(argv))
            run_log_dir = os.path.join(
                self.root_dir, "out", "a", ".reproxy_tmp", "logs",
                "20170316T2000%d.000000_SOME_RANDOM_ID_%d" % (40 + i, i))
            self.assertTrue(os.path.isdir(run_log_dir))
            with open(os.path.join(run_log_dir, "reproxy.rpl"), "w") as f:
                print("Content", file=f)
        log_dir = os.path.join(self.root_dir, "out", "a", ".reproxy_tmp",
                               "logs")
        self.assertTrue(
            os.path.isdir(
                os.path.join(self.root_dir, "out", "a", ".reproxy_tmp",
                             "logs")))
        self.assertTrue(os.path.isdir(log_dir))
        want_remaining_dirs = [
            '20170316T200043.000000_SOME_RANDOM_ID_3',
            '20170316T200046.000000_SOME_RANDOM_ID_6',
            '20170316T200044.000000_SOME_RANDOM_ID_4',
            '20170316T200042.000000_SOME_RANDOM_ID_2',
            '20170316T200045.000000_SOME_RANDOM_ID_5',
        ]
        for p in reclient_helper._test_only_cleanup_logdir_handles:
            p.wait()
        self.assertCountEqual(os.listdir(log_dir), want_remaining_dirs)
        for d in want_remaining_dirs:
            self.assertTrue(
                os.path.isfile(
                    os.path.join(self.root_dir, "out", "a", ".reproxy_tmp",
                                 "logs", d, "reproxy.rpl")))

    @unittest.mock.patch.dict(os.environ, {})
    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', side_effect=KeyboardInterrupt())
    def test_ninja_reclient_ninja_interrupted(self, mock_ninja, mock_call):
        reclient_bin_dir = os.path.join('src', 'buildtools', 'reclient')
        reclient_cfg = os.path.join('src', 'buildtools', 'reclient_cfgs',
                                    'reproxy.cfg')
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join(reclient_bin_dir, 'version.txt'), '0.0')
        write(reclient_cfg, '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(1, ninja_reclient.main(argv))

        mock_ninja.assert_called_once_with(argv)
        mock_call.assert_has_calls([
            unittest.mock.call([
                os.path.join(self.root_dir, reclient_bin_dir,
                             'bootstrap' + gclient_paths.GetExeSuffix()),
                "--re_proxy=" +
                os.path.join(self.root_dir, reclient_bin_dir,
                             'reproxy' + gclient_paths.GetExeSuffix()),
                "--cfg=" + os.path.join(self.root_dir, reclient_cfg)
            ]),
            unittest.mock.call([
                os.path.join(self.root_dir, reclient_bin_dir,
                             'bootstrap' + gclient_paths.GetExeSuffix()),
                "--shutdown",
                "--cfg=" + os.path.join(self.root_dir, reclient_cfg)
            ]),
        ])

    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    def test_ninja_reclient_cfg_not_found(self, mock_ninja, mock_call):
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join('src', 'buildtools', 'reclient', 'version.txt'),
              '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(1, ninja_reclient.main(argv))

        mock_ninja.assert_not_called()
        mock_call.assert_not_called()

    @unittest.mock.patch('subprocess.call', return_value=0)
    @unittest.mock.patch('ninja.main', return_value=0)
    def test_ninja_reclient_bins_not_found(self, mock_ninja, mock_call):
        write('.gclient', '')
        write('.gclient_entries', 'entries = {"buildtools": "..."}')
        write(os.path.join('src', 'buildtools', 'reclient_cfgs', 'reproxy.cfg'),
              '0.0')
        argv = ["ninja_reclient.py", "-C", "out/a", "chrome"]

        self.assertEqual(1, ninja_reclient.main(argv))

        mock_ninja.assert_not_called()
        mock_call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
