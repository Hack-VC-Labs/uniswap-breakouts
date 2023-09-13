import pickle
import logging
from typing import Optional
import urllib.parse

import requests
from web3 import Web3

from uniswap_breakouts.utils.env_utils import get_env_variable
from uniswap_breakouts.config.load import get_chain_resource

logger = logging.getLogger(__name__)


CACHING = False
try:
    caching_env_var = get_env_variable("CASHING")
    if caching_env_var == 'TRUE':
        logger.info("ABI Caching as been Enabled")
        CACHING = True
except ValueError:
    pass


def get_w3_provider(chain: str) -> Web3:
    logger.debug("getting web3 provider for %s", chain)
    chain_config = get_chain_resource(chain)
    return Web3(Web3.HTTPProvider(chain_config.rpc_url))


def construct_scanner_url(chain: str, params: dict) -> str:
    chain_config = get_chain_resource(chain)
    base_url = chain_config.scanner_base_url
    scanner_api_key = chain_config.scanner_api_key
    url = f'{base_url}?{urllib.parse.urlencode(params)}&apikey={scanner_api_key}'
    return url


def extract_json_or_except(response: requests.Response) -> dict:
    try:
        return response.json()['result']
    except requests.exceptions.JSONDecodeError as exc:
        logger.error("Error decoding json in ABI request response: %s", response.text)
        raise exc


def get_abi(chain: str, address: str) -> dict:
    abi_request_params = {"module": "contract", "action": "getabi", "address": address}

    url = construct_scanner_url(chain, abi_request_params)
    logger.debug("constructed url for abi request: %s", url)

    if CACHING:
        cache_path = get_env_variable("CACHE_PATH")
        logger.debug("accessing abi cache path at %s", cache_path)
        try:
            with open(cache_path, 'rb') as pickle_file:
                past_requests = pickle.load(pickle_file)
                logger.debug("cache loaded successfully")
        except FileNotFoundError:
            logger.debug("no cache found at %s, cache will be created", cache_path)
            past_requests = {}
        if url in past_requests.keys():
            abi = past_requests[url]
            logger.debug("abi found in cache")
        else:
            logger.debug("abi not found in cache, requesting from scanner")
            abi_response = requests.get(url, timeout=10)
            abi = extract_json_or_except(abi_response)
            past_requests[url] = abi
            logger.debug("abi request returned, adding to cache")
            with open(cache_path, 'wb') as pickle_file:
                pickle.dump(past_requests, pickle_file)
    else:
        logger.debug("caching is off. requesting from scanner")
        abi_response = requests.get(url, timeout=10)
        abi = extract_json_or_except(abi_response)

    return abi


# this is the number of arguments necessary to make a contract call
# pylint: disable=too-many-arguments
def contract_call_at_block(
    chain: str,
    interface_address: str,
    implementation_address: str,
    fn_name: str,
    fn_args: list,
    block_no: Optional[int] = None,
    abi=None,
):
    logger.debug(
        "making contract call: %s %s %s %s %s",
        chain,
        interface_address,
        fn_name,
        fn_args,
        f" at block {block_no}" if block_no is not None else "",
    )
    w3_provider = get_w3_provider(chain)

    if not abi:
        abi = get_abi(chain, implementation_address)
    contract = w3_provider.eth.contract(address=Web3.to_checksum_address(interface_address), abi=abi)

    contract_fn = getattr(contract.functions, fn_name)
    logger.debug("making contract call")
    if block_no is None:
        res = contract_fn(*fn_args).call()
    else:
        res = contract_fn(*fn_args).call(block_identifier=block_no)
    logger.debug("contract call yielded result: %s", res)
    return res
