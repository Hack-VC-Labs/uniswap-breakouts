import json
import logging
from typing import Dict, List, Optional

from uniswap_breakouts.config.load import get_position_specs
from uniswap_breakouts.uniswap import v2, v3

logger = logging.getLogger(__name__)


def create_position_reports(out_file: Optional[str]):
    position_specs = get_position_specs()
    report_dict: Dict[str, List[Dict[str, dict]]] = {'V2 Positions': [], 'V3 Positions': []}

    for v2_spec in position_specs.v2_positions:
        if v2_spec.wallet_address is not None:
            logger.info("generating v2 position snapshot from wallet: %s", v2_spec.to_dict())
            v2_position_snapshot = v2.get_underlying_balances_from_address(
                v2_spec.chain, v2_spec.pool_address, v2_spec.wallet_address, v2_spec.block_no
            )
        else:
            assert v2_spec.lp_balance is not None
            logger.info("generating v2 position snapshot from lp balance: %s", v2_spec.to_dict())
            v2_position_snapshot = v2.get_underlying_balances_from_lp_balance(
                v2_spec.chain, v2_spec.pool_address, v2_spec.lp_balance, v2_spec.block_no
            )

        report_dict['V2 Positions'].append(
            {'position_spec': v2_spec.to_dict(), 'position_breakdown': v2_position_snapshot.to_dict()}
        )

    for v3_spec in position_specs.v3_positions:
        logger.info("generating v3 snapshot: %s", v3_spec)
        v3_position_snapshot = v3.get_underlying_balances(
            v3_spec.chain,
            v3_spec.pool_address,
            v3_spec.nft_address,
            v3_spec.nft_address,
            v3_spec.nft_id,
            v3_spec.block_no,
        )
        report_dict['V3 Positions'].append(
            {'position_spec': v3_spec.to_dict(), 'position_breakdown': v3_position_snapshot.to_dict()}
        )

    if out_file is not None:
        with open(out_file, 'w', encoding='utf-8') as report_output_file:
            json.dump(report_dict, report_output_file, indent=4, default=str)
    else:
        print(json.dumps(report_dict, indent=2, default=str))
