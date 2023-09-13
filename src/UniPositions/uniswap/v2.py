from typing import Optional

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from decimal import Decimal

from UniPositions.constants.w3 import E18
from UniPositions.uniswap.uniswap_utils import PoolToken, get_pool_token_info
from UniPositions.utils.web3_utils import contract_call_at_block


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


def get_underlying_balances_from_address(chain: str, pool_address: str, wallet_address: str, block_no: Optional[int] = None) -> V2LiquiditySnapshot:
    wallet_lp_balance_result = contract_call_at_block(chain=chain,
                                                      interface_address=pool_address,
                                                      implementation_address=pool_address,
                                                      fn_name='balanceOf',
                                                      fn_args=[wallet_address],
                                                      block_no=block_no)
    wallet_lp_balance = Decimal(wallet_lp_balance_result) / E18

    return get_underlying_balances_from_lp_balance(chain, pool_address, wallet_lp_balance, block_no)


def get_underlying_balances_from_lp_balance(chain: str, pool_address: str, wallet_lp_balance: Decimal, block_no: Optional[int]) -> V2LiquiditySnapshot:
    token0 = get_pool_token_info(pool_address, 0)
    token1 = get_pool_token_info(pool_address, 1)

    pool_total_supply_result = contract_call_at_block(chain=chain,
                                                      interface_address=pool_address,
                                                      implementation_address=pool_address,
                                                      fn_name='totalSupply',
                                                      fn_args=[],
                                                      block_no=block_no)
    pool_total_supply = Decimal(pool_total_supply_result) / E18

    reserves_result = contract_call_at_block(chain=chain,
                                             interface_address=pool_address,
                                             implementation_address=pool_address,
                                             fn_name='getReserves',
                                             fn_args=[],
                                             block_no=block_no)
    token0_reserves = Decimal(reserves_result[0]) / Decimal(10 ** token0.decimals)
    token1_reserves = Decimal(reserves_result[1]) / Decimal(10 ** token1.decimals)

    wallet_share_of_lp = wallet_lp_balance / pool_total_supply
    token0_underlying_lp = token0_reserves * wallet_share_of_lp
    token1_underlying_lp = token1_reserves * wallet_share_of_lp

    return V2LiquiditySnapshot(chain, block_no, wallet_lp_balance, token0, token0_underlying_lp, token1, token1_underlying_lp)
