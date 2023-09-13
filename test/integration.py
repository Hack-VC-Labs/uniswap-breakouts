import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
from typing import Dict, Optional, List
import unittest

PACKAGE_RUN = ["-m", "uniswap_breakouts"]


def run_and_return_std_out(args: Optional[List[str]] = None, env_vars: Optional[Dict[str, str]] = None):
    cmd = [sys.executable] + PACKAGE_RUN
    if args is not None:
        cmd.extend(args)
    env = os.environ.copy()
    if env_vars is not None:
        env.update(env_vars)
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
    process.wait()
    process_std_out_str = process.stdout.read().decode('utf-8')
    process.stdout.close()
    return process_std_out_str


class WethUsdcPoolsCase(unittest.TestCase):
    def setUp(self) -> None:
        self.position_config_path = str(Path(__file__).parent / "test_position_configs/weth_usdc_positions.json")
        self.chain_config_path = str(Path(__file__).parent / "test_chain_resource_configs/default.toml")
        self.expected_output_path = str(Path(__file__).parent / "test_expected_outputs/weth_usdc_expected.json")
        self.out_file_path = str(Path(__file__).parent / "test_outputs/weth_usdc_out.json")
        self.caching_path = str(Path(__file__).parent / "test_caching_dir/weth_usdc_abi_cache.pkl")


        if os.path.exists(self.out_file_path):
            os.remove(self.out_file_path)

        if os.path.exists(self.caching_path):
            os.remove(self.caching_path)

        with open(self.expected_output_path) as expected_file:
            self.expected_output = json.load(expected_file)

    def test_set_configs_in_env(self):
        env_vars = {
            "CHAIN_CONFIG_PATH": self.chain_config_path,
            "POSITION_CONFIG_PATH": self.position_config_path
        }
        raw_output = run_and_return_std_out(env_vars=env_vars)
        actual_output = json.loads(raw_output)

        self.assertEqual(actual_output, self.expected_output)

    def test_set_config_in_cmd_line(self):
        cmd_line_params = ['-c', self.chain_config_path, '-p', self.position_config_path]
        raw_output = run_and_return_std_out(args=cmd_line_params)
        actual_output = json.loads(raw_output)

        self.assertEqual(actual_output, self.expected_output)

    def test_output_to_file(self):
        env_vars = {
            "CHAIN_CONFIG_PATH": self.chain_config_path,
            "POSITION_CONFIG_PATH": self.position_config_path
        }
        cmd_line_params = ['-o', self.out_file_path]
        raw_output = run_and_return_std_out(args=cmd_line_params, env_vars=env_vars)
        self.assertEqual(raw_output, '')

        with open(self.out_file_path) as out_file:
            actual_output = json.load(out_file)

        self.assertEqual(actual_output, self.expected_output)

    def test_set_configs_in_env_with_caching(self):
        env_vars = {
            "CHAIN_CONFIG_PATH": self.chain_config_path,
            "POSITION_CONFIG_PATH": self.position_config_path,
            "CACHING": "TRUE",
            "CACHE_PATH": self.caching_path
        }
        raw_output = run_and_return_std_out(env_vars=env_vars)
        actual_output = json.loads(raw_output)

        self.assertEqual(actual_output, self.expected_output)

        v2_url = 'https://api.etherscan.io/api?module=contract&action=getabi&address=0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'
        v3_url = 'https://api.etherscan.io/api?module=contract&action=getabi&address=0xC36442b4a4522E871399CD717aBDD847Ab11FE88'

        with open(self.caching_path, 'rb') as pickle_cache:
            cached_requests = pickle.load(pickle_cache)
            self.assertEqual(len(cached_requests), 2)
            for cache_url in cached_requests.keys():
                self.assertTrue(v2_url in cache_url or v3_url in cache_url)
