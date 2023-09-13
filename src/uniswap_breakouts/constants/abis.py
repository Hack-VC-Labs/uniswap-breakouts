import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


token_abi_path = Path(__file__).parent / 'token_contract_abi.json'
with open(token_abi_path, encoding='utf-8') as token_abi_file:
    logger.debug("loading ERC20 token contract abi from %s", token_abi_path)
    TOKEN_CONTRACT_ABI = json.load(token_abi_file)


v3_pool_abi_path = Path(__file__).parent / 'v3_pool_abi.json'
with open(v3_pool_abi_path, encoding='utf-8') as v3_abi_file:
    logger.debug("loading V3 pool contract abi from %s", v3_pool_abi_path)
    V3_POOL_CONTRACT_ABI = json.load(v3_abi_file)
