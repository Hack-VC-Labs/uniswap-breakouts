import logging
from typing import List, Optional

import toml

from uniswap_breakouts.config.datatypes import ChainResources, PositionSpecs, PositionSpecsSchema
from uniswap_breakouts.utils.env_utils import get_env_variable

logger = logging.getLogger(__name__)


chain_resource_config_path: Optional[str] = None
chain_resources: Optional[List[ChainResources]] = None
position_spec_config_path: Optional[str] = None
position_specs: Optional[PositionSpecs] = None


def set_chain_resource_config_path(path: str) -> None:
    global chain_resource_config_path
    assert chain_resource_config_path is None, "chain resource config path was already set"
    logger.info(f"setting chain resource config file to {path}")
    chain_resource_config_path = path


def set_chain_resource_config_path_from_env() -> None:
    global chain_resource_config_path
    try:
        logger.debug("attempting to get chain config path from environment variable CHAIN_CONFIG_PATH")
        config_path = get_env_variable("CHAIN_CONFIG_PATH")
    except ValueError:
        logger.error("Chain config path must be set via the commandline or environment")
        raise ValueError("Chain config path not set")
    set_chain_resource_config_path(config_path)


def get_chain_resources() -> List[ChainResources]:
    global chain_resources
    if chain_resources is not None:
        logger.debug("using cached chain resources config")
        return chain_resources

    if chain_resource_config_path is None:
        logger.debug("chain resource config path is not set, attempting to get it from environment")
        set_chain_resource_config_path_from_env()

    logger.info(f"loading chain resource config from {chain_resource_config_path}")
    with open(chain_resource_config_path) as chain_config_file:
        chain_resource_config = toml.load(chain_config_file)

    chain_resources = [ChainResources(**chain) for chain in chain_resource_config['chains']]
    logger.debug(f"chain resource config successfully loaded from {chain_resource_config_path}")
    return chain_resources


def get_chain_resource(chain: str) -> ChainResources:
    logger.debug(f'getting chain resources for {chain}')
    configs = get_chain_resources()
    for config in configs:
        if chain == config.name:
            return config

    raise ValueError(f'chain not found in config: {chain}')


def set_position_spec_config_path(path: str) -> None:
    global position_spec_config_path
    assert position_spec_config_path is None, "position spec config path was already set"
    logger.info(f"setting position config path to {path}")
    position_spec_config_path = path


def set_position_spec_config_path_from_env() -> None:
    try:
        logger.debug("attempting to get position spec config path from environment variable POSITION_CONFIG_PATH")
        position_config = get_env_variable("POSITION_CONFIG_PATH")
    except ValueError:
        logger.error("Position config path must be set via the commandline or environment")
        raise ValueError("Position config path not set")
    set_position_spec_config_path(position_config)


def get_position_specs() -> PositionSpecs:
    global position_specs
    if position_specs is not None:
        logger.debug('using cached position config')
        return position_specs

    if position_spec_config_path is None:
        logger.debug("position spec config path is not set, attempting to get it from environment")
        set_position_spec_config_path_from_env()

    logger.info(f'loading position config from {position_spec_config_path}')
    with open(position_spec_config_path) as position_spec_config_file:
        position_specs = PositionSpecsSchema().loads(position_spec_config_file.read())

    logger.debug(f"position config successfully loaded from {position_spec_config_path}")
    return position_specs
