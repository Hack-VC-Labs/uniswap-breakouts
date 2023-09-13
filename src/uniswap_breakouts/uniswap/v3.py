from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Optional, Tuple

from dataclasses_json import dataclass_json

from uniswap_breakouts.uniswap.uniswap_utils import PoolToken, get_pool_token_info
from uniswap_breakouts.utils.web3_utils import contract_call_at_block

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass(frozen=True)
class V3LiquiditySnapshot:
    chain: str
    block: Optional[int]
    token_id: int
    current_ratio: Decimal
    lower_tick: Decimal
    upper_tick: Decimal
    token0: PoolToken
    num_token0_underlying: Decimal
    token1: PoolToken
    num_token1_underlying: Decimal


def pool_string(chain: str, pool_address: str, nft_id: int, block_no: Optional[int]) -> str:
    return f"{chain} - {pool_address} id: {nft_id}" + (f" at block {block_no}" if block_no is not None else "")


def q64_96_to_decimal(q64_96_number: int) -> Decimal:
    return Decimal(q64_96_number) / Decimal(2**96)


def tick_to_price(tick_index: int) -> Decimal:
    return Decimal('1.0001') ** tick_index


def price_outside_below(tick_lower: Decimal, tick_upper: Decimal, liquidity: Decimal) -> Decimal:
    return liquidity * (tick_upper.sqrt() - tick_lower.sqrt()) / (tick_lower.sqrt() * tick_lower.sqrt())


def price_outside_above(tick_lower: Decimal, tick_upper: Decimal, liquidity: Decimal) -> Decimal:
    return liquidity * (tick_upper.sqrt() - tick_lower.sqrt())


def price_inbetween(price: Decimal, tick_lower: Decimal, tick_upper: Decimal, liquidity: Decimal) -> Tuple[Decimal, Decimal]:
    token0_position_virtual = liquidity * (tick_upper.sqrt() - price.sqrt()) / (price.sqrt() * tick_lower.sqrt())
    token1_position_virtual = liquidity * (price.sqrt() - tick_lower.sqrt())
    return token0_position_virtual, token1_position_virtual


def get_underlying_balances(chain: str, pool_address: str, nft_address: str, nft_impl_address: str, nft_id: int, block_no: Optional[int] = None) -> V3LiquiditySnapshot:
    def position_string() -> str:
        return pool_string(chain, pool_address, nft_id, block_no)

    logger.debug(f"requesting underlying LP balances for V3 position f{position_string()}")
    token0 = get_pool_token_info(chain, pool_address, 0)
    token1 = get_pool_token_info(chain, pool_address, 1)
    decimal_adjustment = Decimal(10 ** (token0.decimals - token1.decimals))

    logger.debug(f"getting pool price for {position_string()}")
    pool_info_result = contract_call_at_block(chain=chain,
                                              interface_address=pool_address,
                                              implementation_address=pool_address,
                                              fn_name='slot0',
                                              fn_args=[],
                                              block_no=block_no)

    sqrt_price_x96 = pool_info_result[0]
    price = q64_96_to_decimal(sqrt_price_x96) ** Decimal(2)
    logger.info(f"price of {price} for pool {position_string()}")

    logger.debug(f"requesting position details for {position_string()}")
    positions_info_result = contract_call_at_block(chain=chain,
                                                   interface_address=nft_address,
                                                   implementation_address=nft_impl_address,
                                                   fn_name='positions',
                                                   fn_args=[nft_id],
                                                   block_no=block_no)

    tick_lower = positions_info_result[5]
    lower_tick_price = tick_to_price(tick_lower)
    tick_upper = positions_info_result[6]
    upper_tick_price = tick_to_price(tick_upper)
    liquidity = positions_info_result[7]
    logger.info(f"position details: lower {lower_tick_price} | upper {upper_tick_price} | liquidity {liquidity} "
                f"for {position_string()}")

    if price > upper_tick_price:
        logger.debug(f"calculating underlying for price above upper tick for {position_string()}")
        token0_position_virtual = Decimal(0)
        token1_position_virtual = price_outside_above(lower_tick_price, upper_tick_price, Decimal(liquidity))
    elif price < lower_tick_price:
        logger.debug(f"calculating underlying for price below lower tick for {position_string()}")
        token0_position_virtual = price_outside_below(lower_tick_price, upper_tick_price, Decimal(liquidity))
        token1_position_virtual = Decimal(0)
    else:
        logger.debug(f"calculating underlying for price between ticks for {position_string()}")
        token0_position_virtual, token1_position_virtual = price_inbetween(price, lower_tick_price, upper_tick_price, Decimal(liquidity))

    token0_position = token0_position_virtual / Decimal(10 ** token0.decimals)
    token1_position = token1_position_virtual / Decimal(10 ** token1.decimals)
    logger.info(f"underlying positions of token0 - {token0_position} and token1 - {token1_position}"
                f" for {position_string()}")

    snapshot = V3LiquiditySnapshot(chain=chain,
                                   block=block_no,
                                   token_id=nft_id,
                                   current_ratio=price * decimal_adjustment,
                                   lower_tick=lower_tick_price * decimal_adjustment,
                                   upper_tick=upper_tick_price * decimal_adjustment,
                                   token0=token0,
                                   num_token0_underlying=token0_position,
                                   token1=token1,
                                   num_token1_underlying=token1_position,
                                   )
    return snapshot
