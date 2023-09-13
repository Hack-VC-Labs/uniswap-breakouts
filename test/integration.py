import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, Optional, List
import unittest

MAIN_MODULE = Path(__file__).parent / "../src/uniswap_breakouts/main.py"


def run_and_return_std_out(args: Optional[List[str]] = None, env_vars: Optional[Dict[str, str]] = None):
    cmd = [sys.executable, MAIN_MODULE]
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
        out_file_path = str(Path(__file__).parent / "test_outputs/weth_usdc_out.json")
        cmd_line_params = ['-o', out_file_path]
        raw_output = run_and_return_std_out(args=cmd_line_params, env_vars=env_vars)
        self.assertEqual(raw_output, '')

        with open(out_file_path) as out_file:
            actual_output = json.load(out_file)

        self.assertEqual(actual_output, self.expected_output)