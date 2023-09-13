from typing import List, Optional

import toml

from uniswap_breakouts.config.datatypes import ChainResources, PositionSpecs, PositionSpecsSchema

chain_resource_config_path: Optional[str] = None
chain_resources: Optional[List[ChainResources]] = None
position_spec_config_path: Optional[str] = None
position_specs: Optional[PositionSpecs] = None


def set_chain_resource_config_path(path: str) -> None:
    global chain_resource_config_path
    assert chain_resource_config_path is None, "chain resource config path was already set"
    chain_resource_config_path = path


def get_chain_resources() -> List[ChainResources]:
    global chain_resources
    if chain_resources is not None:
        return chain_resources

    #chain_resource_config_path = get_env_variable("CHAIN_CONFIG_PATH")
    assert chain_resource_config_path is not None

    with open(chain_resource_config_path) as chain_config_file:
        chain_resource_config = toml.load(chain_config_file)

    chain_resources = [ChainResources(**chain) for chain in chain_resource_config['chains']]
    return chain_resources


def get_chain_resource(chain: str) -> ChainResources:
    configs = get_chain_resources()
    for config in configs:
        if chain == config.name:
            return config

    raise ValueError(f'chain not found in config: {chain}')


def set_position_spec_config_path(path: str) -> None:
    global position_spec_config_path
    assert position_spec_config_path is None, "position spec config path was already set"
    position_spec_config_path = path


def get_position_specs() -> PositionSpecs:
    global position_specs
    if position_specs is not None:
        return position_specs

    assert position_spec_config_path is not None

    with open(position_spec_config_path) as position_spec_config_file:
        position_specs = PositionSpecsSchema().loads(position_spec_config_file.read())

    return position_specs
