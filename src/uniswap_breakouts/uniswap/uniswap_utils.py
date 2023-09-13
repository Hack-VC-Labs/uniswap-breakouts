from dataclasses import dataclass
import logging

from dataclasses_json import dataclass_json

from uniswap_breakouts.constants.abis import TOKEN_CONTRACT_ABI
from uniswap_breakouts.utils.web3_utils import contract_call_at_block

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass(frozen=True)
class PoolToken:
    index: int
    address: str
    symbol: str
    decimals: int


def get_pool_token_info(chain: str, pool_address: str, token_index: int) -> PoolToken:
    assert token_index == 0 or token_index == 1
    logger.debug(f"getting token info for pool {chain} - {pool_address} with token index {token_index}")

    fn_name = f"token{token_index}"

    token_address = contract_call_at_block(interface_address=pool_address,
                                           implementation_address=pool_address,
                                           fn_name=fn_name,
                                           fn_args=[],
                                           chain=chain)

    token_decimals = contract_call_at_block(interface_address=token_address,
                                            implementation_address=token_address,
                                            fn_name='decimals',
                                            fn_args=[],
                                            chain=chain,
                                            abi=TOKEN_CONTRACT_ABI)

    token_symbol = contract_call_at_block(interface_address=token_address,
                                          implementation_address=token_address,
                                          fn_name='symbol',
                                          fn_args=[],
                                          chain=chain,
                                          abi=TOKEN_CONTRACT_ABI)

    pool_token = PoolToken(token_index, token_address, token_symbol, int(token_decimals))
    logger.debug(f"successfully pulled pool token info: {pool_token.to_dict()}")
    return pool_token

