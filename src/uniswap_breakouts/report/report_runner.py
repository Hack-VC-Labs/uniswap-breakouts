import json
import logging
from typing import List, Tuple

from uniswap_breakouts.config.load import get_position_specs
from uniswap_breakouts.uniswap import v2, v3

logger = logging.getLogger(__name__)


def create_position_reports():
    position_specs = get_position_specs()

    v2_report: List[Tuple[dict, dict]] = []
    for v2_spec in position_specs.v2_positions:
        if v2_spec.wallet_address is not None:
            logger.info(f'generating v2 position snapshot from wallet: {v2_spec.to_dict()}')
            position_snapshot = v2.get_underlying_balances_from_address(v2_spec.chain,
                                                                        v2_spec.pool_address,
                                                                        v2_spec.wallet_address,
                                                                        v2_spec.block_no)
        else:
            assert v2_spec.lp_balance is not None
            logger.info(f'generating v2 position snapshot from lp balance: {v2_spec.to_dict()}')
            position_snapshot = v2.get_underlying_balances_from_lp_balance(v2_spec.chain,
                                                                           v2_spec.pool_address,
                                                                           v2_spec.lp_balance,
                                                                           v2_spec.block_no)

        v2_report.append((v2_spec.to_dict(), position_snapshot.to_dict()))

    v3_report: List[Tuple[dict, dict]] = []
    for v3_spec in position_specs.v3_positions:
        logger.info(f'generating v3 snapshot: {v3_spec}')
        position_snapshot = v3.get_underlying_balances(v3_spec.chain,
                                                       v3_spec.pool_address,
                                                       v3_spec.nft_address,
                                                       v3_spec.nft_address,
                                                       v3_spec.nft_id,
                                                       v3_spec.block_no)
        v3_report.append((v3_spec.to_dict(), position_snapshot.to_dict()))

    logger.debug("done generating snapshots. printing report")
    print("V2 Positions")
    print()
    for spec, snapshot in v2_report:
        print(json.dumps(spec, indent=4, default=str))
        print()
        print(json.dumps(snapshot, indent=4, default=str))
        print()
        print()

    print("V3 Positions")
    print()
    for spec, snapshot in v3_report:
        print(json.dumps(spec, indent=4, default=str))
        print()
        print(json.dumps(snapshot, indent=4, default=str))
        print()
        print()
