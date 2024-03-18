from decimal import Decimal
import os
from pathlib import Path
import unittest

import pandas as pd

from uniswap_breakouts.uniswap import v3_ticks


class V3TicksUnitCase(unittest.TestCase):
    def setUp(self) -> None:
        self.chain_config_path = str(Path(__file__).parent / "test_chain_resource_configs/default.toml")
        self.expected_output_path = str(
            Path(__file__).parent / "test_expected_outputs/weth_btc_expected_df.csv"
        )
        self.out_file_path = str(Path(__file__).parent / "test_outputs/weth_btc_out.csv")

        if os.path.exists(self.out_file_path):
            os.remove(self.out_file_path)

        os.environ["CHAIN_CONFIG_PATH"] = self.chain_config_path

    def test_liquidity_snapshot_and_df(self):
        liquidity_snapshot = v3_ticks.get_tick_liquidity_info_for_pool(
            chain='ethereum',
            pool_address='0xCBCdF9626bC03E24f779434178A73a0B4bad62eD',  # weth-btc 30bps pool
            tick_lens_address='0xbfd8137f7d1516D3ea5cA83523914859ec47F573',  # ethereum ticklens address
            block_no=18086348,
            depth=Decimal(0.025),
        )

        ticks_df = v3_ticks.make_tick_liquidity_df(liquidity_snapshot, depth=Decimal(0.025))
        ticks_df.to_csv(self.out_file_path)

        # write and read to CSV for easy comparison and inspection, and because we plan to store these as CSVs
        actual_ticks_df = pd.read_csv(self.out_file_path, index_col=0)
        expected_ticks_df = pd.read_csv(self.expected_output_path, index_col=0)

        comp = actual_ticks_df.compare(expected_ticks_df)
        self.assertTrue(comp.empty)

        self.assertEqual(liquidity_snapshot.chain, 'ethereum')
        self.assertEqual(liquidity_snapshot.block, 18086348)
        self.assertEqual(liquidity_snapshot.virtual_ratio, Decimal('157787770847.5234530587784276'))
        self.assertEqual(liquidity_snapshot.active_tick, 257858)
        self.assertEqual(liquidity_snapshot.active_liquidity, 2053104318434531812)
        self.assertEqual(liquidity_snapshot.tick_spacing, 60)

        self.assertEqual(liquidity_snapshot.token0.index, 0)
        self.assertEqual(liquidity_snapshot.token0.address, '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599')
        self.assertEqual(liquidity_snapshot.token0.symbol, 'WBTC')
        self.assertEqual(liquidity_snapshot.token0.decimals, 8)

        self.assertEqual(liquidity_snapshot.token1.index, 1)
        self.assertEqual(liquidity_snapshot.token1.address, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
        self.assertEqual(liquidity_snapshot.token1.symbol, 'WETH')
        self.assertEqual(liquidity_snapshot.token1.decimals, 18)
