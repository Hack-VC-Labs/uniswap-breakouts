import typing
from dataclasses import dataclass
from decimal import Decimal
import logging
import math
from typing import Optional, List

from dataclasses_json import DataClassJsonMixin
import pandas as pd
import numpy as np

from uniswap_breakouts.constants.abis import V3_POOL_CONTRACT_ABI
from uniswap_breakouts.constants.uni_v3 import TICK_BITMAP_ARRAY_LENGTH
from uniswap_breakouts.uniswap.uniswap_utils import PoolToken, get_pool_token_info
from uniswap_breakouts.uniswap.v3 import (
    q64_96_to_decimal,
    tick_to_price,
    get_virtual_underlyings_from_range,
    get_price_info_for_pool,
)
from uniswap_breakouts.utils.web3_utils import contract_call_at_block

logger = logging.getLogger(__name__)

BPS_PER_100 = 10000


@dataclass(frozen=True)
class TickLiquidityInfo:
    tick: int
    liquidity_net: int
    liquidity_gross: int


@dataclass(frozen=True)
class V3TickLiquiditySnapshot(DataClassJsonMixin):
    # pylint: disable=too-many-instance-attributes
    # there isn't a logical place to group these differently
    chain: str
    block: Optional[int]
    virtual_ratio: Decimal
    active_tick: int
    active_liquidity: int
    token0: PoolToken
    token1: PoolToken
    tick_spacing: int
    ticks: List[TickLiquidityInfo]


def pool_string(chain: str, pool_address: str, block_no: Optional[int]) -> str:
    return f"{chain} - {pool_address}" + (f" at block {block_no}" if block_no is not None else "")


def get_initialized_tick_info(  # pylint: disable=too-many-arguments
    chain: str,
    pool_address: str,
    tick_lens_address: str,
    active_tick: int,
    tick_spacing: int,
    depth: Decimal,
    block_no: Optional[int] = None,
) -> List[TickLiquidityInfo]:
    """
    Request liquidity information on ticks around the current tick from the tick lens

    The tick lens contract offers one function, getPopulatedTicksInWord, which returns all the initialized
    ticks in a bitmap word, along with information about their liquidity. We first find the bitmap word of the
    active tick, then request the ticks above and below that word, depending on the depth of book we are
    interested in.

    See the Uniswap V3 book for more information on the bitmap structure.

    We are particularly interested in getting the 'liquidityNet' for each tick. This field tells us the
    difference in `liquidity` between the tick and the previous tick. We know the `liquidity` in the active
    tick, so we can derive the liquidity in all surrounding ticks using 'liquidityNet' later.
    """

    # concentrated liquidity bands can only start and stop at ticks divisible by the pool's `tick_spacing`
    # the bitmap only indexes 'spaced' ticks, we find the index of the adjacent spaced tick by int division
    bitmap_current_tick_index = active_tick // tick_spacing
    bitmap_current_tick_word_index = bitmap_current_tick_index // TICK_BITMAP_ARRAY_LENGTH

    # each tick basically equates to 1bp, a word in the bitmap will index 256 ticks and only includes spaced
    # ticks. This approximation works ok for small numbers. We round up to ensure we get everything we need
    word_depth = math.ceil(depth * BPS_PER_100 / (TICK_BITMAP_ARRAY_LENGTH * tick_spacing))

    initialized_tick_list: List[TickLiquidityInfo] = []
    # iterate backwards since the ticks come in descending order from the contract within a word
    for i in range(
        bitmap_current_tick_word_index + word_depth, bitmap_current_tick_word_index - (word_depth + 1), -1
    ):
        initialized_ticks_in_word_response = contract_call_at_block(
            chain=chain,
            interface_address=tick_lens_address,
            implementation_address=tick_lens_address,
            fn_name='getPopulatedTicksInWord',
            fn_args=[pool_address, i],
            block_no=block_no,
            abi=None,
        )
        initialized_ticks_in_word = [
            TickLiquidityInfo(*tick_info) for tick_info in initialized_ticks_in_word_response
        ]
        initialized_tick_list.extend(initialized_ticks_in_word)

    return initialized_tick_list


def get_tick_liquidity_info_for_pool(
    chain: str, pool_address: str, tick_lens_address: str, depth: Decimal, block_no: Optional[int] = None
) -> V3TickLiquiditySnapshot:
    def pool_str() -> str:
        return pool_string(chain, pool_address, block_no)

    logger.debug("requesting pool tick liquidity info for pool %s", pool_str())
    token0 = get_pool_token_info(chain, pool_address, 0, V3_POOL_CONTRACT_ABI)
    token1 = get_pool_token_info(chain, pool_address, 1, V3_POOL_CONTRACT_ABI)

    logger.debug("getting pool price information for pool %s", pool_str())
    pool_info_result = get_price_info_for_pool(chain, pool_address, block_no)

    # We calculate the virtual ratio here, which means it is not yet adjusted to the
    # tokens decimals. This is because the virtual ratio is used in downstream calculations
    # and the decimal-adjusted ratio is necessary for display
    sqrt_price_x96 = int(pool_info_result[0])
    virtual_ratio = q64_96_to_decimal(sqrt_price_x96) ** Decimal(2)

    active_tick = int(pool_info_result[1])

    logger.debug("getting active liquidity for pool %s", pool_str())
    active_liquidity = contract_call_at_block(
        chain=chain,
        interface_address=pool_address,
        implementation_address=pool_address,
        fn_name='liquidity',
        fn_args=[],
        block_no=block_no,
        abi=V3_POOL_CONTRACT_ABI,
    )
    assert isinstance(active_liquidity, int)

    logger.debug("getting tick spacing for pool %s", pool_str())
    tick_spacing = contract_call_at_block(
        chain=chain,
        interface_address=pool_address,
        implementation_address=pool_address,
        fn_name='tickSpacing',
        fn_args=[],
        block_no=block_no,
        abi=V3_POOL_CONTRACT_ABI,
    )
    assert isinstance(tick_spacing, int)

    logger.debug("getting initialized ticks around the current range for pool %s", pool_str())
    ticks = get_initialized_tick_info(
        chain, pool_address, tick_lens_address, active_tick, tick_spacing, depth, block_no
    )

    return V3TickLiquiditySnapshot(
        chain=chain,
        block=block_no,
        virtual_ratio=virtual_ratio,
        active_tick=active_tick,
        active_liquidity=active_liquidity,
        token0=token0,
        token1=token1,
        tick_spacing=tick_spacing,
        ticks=ticks,
    )


@typing.no_type_check  # mypy and pandas/Decimal is weird. The function works and its just for users
def make_tick_liquidity_df(snapshot: V3TickLiquiditySnapshot, depth: Decimal) -> pd.DataFrame:
    # reverse order of ticks since we want to cumulatively sum in increasing order
    logger.debug("calculating liquidity metrics")
    tick_df = pd.DataFrame(reversed([vars(tick) for tick in snapshot.ticks]))  # type: ignore

    # fill in missing ticks so the dataframe is not sparse
    all_ticks = pd.DataFrame(
        {'tick': np.arange(tick_df['tick'].min(), tick_df['tick'].max(), snapshot.tick_spacing)}
    )
    tick_df = pd.merge_ordered(tick_df, all_ticks, how='outer', on='tick').fillna(0)

    # "liquidity_net" represents the difference in liquidity between adjacent ticks. We take a cumulative
    # sum to get the shape of the liquidity profile. We know the liquidity of the active tick, so we use that
    # to adjust the shape of the liquidity to the correct value
    tick_df['liquidity_shape'] = tick_df['liquidity_net'].cumsum()
    active_tick_lower = (snapshot.active_tick // snapshot.tick_spacing) * snapshot.tick_spacing
    net_active_liquidity = tick_df.loc[tick_df['tick'] == active_tick_lower]['liquidity_shape'].values[0]
    liquidity_adjustment = snapshot.active_liquidity - net_active_liquidity
    tick_df['liquidity'] = tick_df['liquidity_shape'] + liquidity_adjustment

    # set up for underlying calculations
    decimal_adjustment = Decimal(10) ** Decimal(snapshot.token0.decimals - snapshot.token1.decimals)
    tick_df['tick_upper'] = tick_df['tick'] + snapshot.tick_spacing
    tick_df['virtual_ratio'] = tick_df['tick'].apply(tick_to_price)
    tick_df['virtual_ratio_upper'] = tick_df['tick_upper'].apply(tick_to_price)
    tick_df['ratio'] = tick_df['virtual_ratio'] * decimal_adjustment
    tick_df['ratio_upper'] = tick_df['virtual_ratio_upper'] * decimal_adjustment

    # Apply the underlying token range function from the v3 module on each tick. We basically treat each tick
    # treat each tick as its own range position
    tick_df[['token0_underlying_virtual', 'token1_underlying_virtual']] = tick_df.apply(
        lambda row: pd.Series(
            get_virtual_underlyings_from_range(
                snapshot.virtual_ratio, row['virtual_ratio'], row['virtual_ratio_upper'], row['liquidity']
            )
        ),
        axis=1,
    )

    tick_df['token0_underlying'] = tick_df['token0_underlying_virtual'] / Decimal(10) ** Decimal(
        snapshot.token0.decimals
    )
    tick_df['token1_underlying'] = tick_df['token1_underlying_virtual'] / Decimal(10) ** Decimal(
        snapshot.token1.decimals
    )

    # Trim df to requested depth
    depth_in_ticks = snapshot.active_tick * depth
    tick_df_trimmed = tick_df.loc[
        (tick_df["tick"] > (snapshot.active_tick - depth_in_ticks))
        & (tick_df["tick"] < (snapshot.active_tick + depth_in_ticks))
    ]
    return tick_df_trimmed
