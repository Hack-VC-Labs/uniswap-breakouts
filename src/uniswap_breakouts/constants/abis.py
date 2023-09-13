import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


token_abi_path = Path(__file__).parent / 'token_contract_abi.json'
with open(token_abi_path) as abi_file:
    logger.debug(f'loading ERC20 token contract abi from {token_abi_path}')
    TOKEN_CONTRACT_ABI = json.load(abi_file)
