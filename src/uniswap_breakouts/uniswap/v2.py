from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from uniswap_breakouts.constants.w3 import E18
from uniswap_breakouts.uniswap.uniswap_utils import PoolToken, get_pool_token_info
from uniswap_breakouts.utils.web3_utils import contract_call_at_block

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class V2LiquiditySnapshot(DataClassJsonMixin):
    chain: str
    block: Optional[int]
    num_lp_tokens: Decimal
    token0: PoolToken
    num_token0_underlying: Decimal
    token1: PoolToken
    num_token1_underlying: Decimal


def pool_string(chain: str, pool_address: str, block_no: Optional[int]) -> str:
    return f"{chain} - {pool_address}" + (f" at block {block_no}" if block_no is not None else "")


def get_underlying_balances_from_address(
    chain: str, pool_address: str, wallet_address: str, block_no: Optional[int] = None
) -> V2LiquiditySnapshot:
    """
    Get underlying LP tokens for an address

    This convenience function just gets the total underlying balance with the `balanceOf()` endpoint
    and then feeds it into the function that does the math. We separate these because we often
    have to get the balance from a different source (i.e. staking contract)
    """
    logger.debug(
        "requesting underlying LP balances for wallet %s in V2 pool %s",
        wallet_address,
        pool_string(chain, pool_address, block_no),
    )
    wallet_lp_balance_result = contract_call_at_block(
        chain=chain,
        interface_address=pool_address,
        implementation_address=pool_address,
        fn_name='balanceOf',
        fn_args=[wallet_address],
        block_no=block_no,
    )
    wallet_lp_balance = Decimal(wallet_lp_balance_result) / E18

    logger.info(
        "returned LP token balance of %s for wallet %s in pool %s",
        wallet_lp_balance,
        wallet_address,
        pool_string(chain, pool_address, block_no),
    )
    return get_underlying_balances_from_lp_balance(chain, pool_address, wallet_lp_balance, block_no)


def get_underlying_balances_from_lp_balance(
    chain: str, pool_address: str, wallet_lp_balance: Decimal, block_no: Optional[int]
) -> V2LiquiditySnapshot:
    """
    Get the underlying balances for a V2 LP position.

    1. Find the total LP token supply - `totalSupply()` of the pool contract
    2. Use these results to find your % share of the pool liquidity
    3. Find the total underlying balances of the pool - `balances()` on the pool contract
    4. Apply your LP share to the total underlying balances to get your claim on the underlying
    """

    def pool_str() -> str:
        return pool_string(chain, pool_address, block_no)

    logger.debug("calculating underlying balances for %s LP Tokens in pool %s", wallet_lp_balance, pool_str())
    token0 = get_pool_token_info(chain, pool_address, 0)
    token1 = get_pool_token_info(chain, pool_address, 1)

    logger.debug("getting total LP supply for %s", pool_str())
    pool_total_supply_result = contract_call_at_block(
        chain=chain,
        interface_address=pool_address,
        implementation_address=pool_address,
        fn_name='totalSupply',
        fn_args=[],
        block_no=block_no,
    )
    pool_total_supply = Decimal(pool_total_supply_result) / E18
    logger.info("total LP supply of %s for %s", pool_total_supply, pool_str())

    logger.debug("getting reserves for %s", pool_str())
    reserves_result = contract_call_at_block(
        chain=chain,
        interface_address=pool_address,
        implementation_address=pool_address,
        fn_name='getReserves',
        fn_args=[],
        block_no=block_no,
    )
    token0_reserves = Decimal(reserves_result[0]) / Decimal(10**token0.decimals)
    token1_reserves = Decimal(reserves_result[1]) / Decimal(10**token1.decimals)
    logger.info(
        "reserves of token0 - %s and token1 - %s for %s", token0_reserves, token1_reserves, pool_str()
    )

    wallet_share_of_lp = wallet_lp_balance / pool_total_supply
    token0_underlying_lp = token0_reserves * wallet_share_of_lp
    token1_underlying_lp = token1_reserves * wallet_share_of_lp
    logger.info(
        "LP Share - %s | token 0 underlying - %s | token 1 underlying - %s",
        wallet_share_of_lp,
        token0_underlying_lp,
        token1_underlying_lp,
    )

    return V2LiquiditySnapshot(
        chain, block_no, wallet_lp_balance, token0, token0_underlying_lp, token1, token1_underlying_lp
    )
