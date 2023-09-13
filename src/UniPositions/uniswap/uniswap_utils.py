import json

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from decimal import Decimal

from UniPositions.constants.abis import TOKEN_CONTRACT_ABI
from UniPositions.utils.web3_utils import contract_call_at_block


@dataclass_json
@dataclass(frozen=True)
class PoolToken:
    index: int
    address: str
    symbol: str
    decimals: int


def get_pool_token_info(pool_address: str, token_index: int) -> PoolToken:
    assert token_index == 0 or token_index == 1
    fn_name = f"token{token_index}"

    token_address: str = contract_call_at_block(interface_address=pool_address,
                                                implementation_address=pool_address,
                                                fn_name=fn_name,
                                                fn_args=[],
                                                chain='ethereum')

    token_decimals = contract_call_at_block(interface_address=token_address,
                                            implementation_address=token_address,
                                            fn_name='decimals',
                                            fn_args=[],
                                            chain='ethereum',
                                            abi=TOKEN_CONTRACT_ABI)

    token_symbol = contract_call_at_block(interface_address=token_address,
                                          implementation_address=token_address,
                                          fn_name='symbol',
                                          fn_args=[],
                                          chain='ethereum',
                                          abi=TOKEN_CONTRACT_ABI)

    return PoolToken(token_index, token_address, token_symbol, int(token_decimals))

