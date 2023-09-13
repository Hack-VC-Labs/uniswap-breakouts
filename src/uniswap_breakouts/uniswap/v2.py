from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Optional

from dataclasses_json import dataclass_json

from uniswap_breakouts.constants.w3 import E18
from uniswap_breakouts.uniswap.uniswap_utils import PoolToken, get_pool_token_info
from uniswap_breakouts.utils.web3_utils import contract_call_at_block

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass(frozen=True)
class V2LiquiditySnapshot:
    chain: str
    block: Optional[int]
    num_lp_tokens: Decimal
    token0: PoolToken
    num_token0_underlying: Decimal
    token1: PoolToken
    num_token1_underlying: Decimal


def pool_string(chain: str, pool_address: str, block_no: Optional[int]) -> str:
    return f"{chain} - {pool_address}" + (f" at block {block_no}" if block_no is not None else "")


def get_underlying_balances_from_address(chain: str, pool_address: str, wallet_address: str, block_no: Optional[int] = None) -> V2LiquiditySnapshot:
    logger.debug(f"requesting underlying LP balances for wallet {wallet_address} in V2 pool "
                 f"{pool_string(chain, pool_address, block_no)}")
    wallet_lp_balance_result = contract_call_at_block(chain=chain,
                                                      interface_address=pool_address,
                                                      implementation_address=pool_address,
                                                      fn_name='balanceOf',
                                                      fn_args=[wallet_address],
                                                      block_no=block_no)
    wallet_lp_balance = Decimal(wallet_lp_balance_result) / E18

    logger.info(f"returned LP token balance of {wallet_lp_balance} for wallet {wallet_address} in pool "
                f"{pool_string(chain, pool_address, block_no)}")
    return get_underlying_balances_from_lp_balance(chain, pool_address, wallet_lp_balance, block_no)


def get_underlying_balances_from_lp_balance(chain: str, pool_address: str, wallet_lp_balance: Decimal, block_no: Optional[int]) -> V2LiquiditySnapshot:
    logger.debug(f"calculating underlying balances for {wallet_lp_balance} LP Tokens in pool "
                 f"{pool_string(chain, pool_address, block_no)}")
    token0 = get_pool_token_info(chain, pool_address, 0)
    token1 = get_pool_token_info(chain, pool_address, 1)

    logger.debug(f"getting total LP supply for {pool_string(chain, pool_address, block_no)}")
    pool_total_supply_result = contract_call_at_block(chain=chain,
                                                      interface_address=pool_address,
                                                      implementation_address=pool_address,
                                                      fn_name='totalSupply',
                                                      fn_args=[],
                                                      block_no=block_no)
    pool_total_supply = Decimal(pool_total_supply_result) / E18
    logger.info(f"total LP supply of {pool_total_supply} for {pool_string(chain, pool_address, block_no)}")

    logger.debug(f"getting reserves for {pool_string(chain, pool_address, block_no)}")
    reserves_result = contract_call_at_block(chain=chain,
                                             interface_address=pool_address,
                                             implementation_address=pool_address,
                                             fn_name='getReserves',
                                             fn_args=[],
                                             block_no=block_no)
    token0_reserves = Decimal(reserves_result[0]) / Decimal(10 ** token0.decimals)
    token1_reserves = Decimal(reserves_result[1]) / Decimal(10 ** token1.decimals)
    logger.info(f"reserves of token0 - {token0_reserves} and token1 - {token1_reserves} for "
                f"{pool_string(chain, pool_address, block_no)}")

    wallet_share_of_lp = wallet_lp_balance / pool_total_supply
    token0_underlying_lp = token0_reserves * wallet_share_of_lp
    token1_underlying_lp = token1_reserves * wallet_share_of_lp
    logger.info(f"LP Share - {wallet_share_of_lp} |"
                f" token 0 underlying - {token1_underlying_lp} |"
                f" token 1 underlying - {token1_underlying_lp}")

    return V2LiquiditySnapshot(chain, block_no, wallet_lp_balance, token0, token0_underlying_lp, token1, token1_underlying_lp)
