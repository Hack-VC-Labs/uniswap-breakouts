from argparse import ArgumentParser
import logging
from typing import Optional

from uniswap_breakouts.config.load import set_chain_resource_config_path, set_position_spec_config_path
from uniswap_breakouts.report.report_runner import create_position_reports
from uniswap_breakouts.utils.env_utils import get_env_variable


def main(verbose: int, chain_config: Optional[str] = None, position_config: Optional[str] = None) -> None:
    log_verbosity = [logging.ERROR, logging.INFO, logging.DEBUG]
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log_verbosity[verbose])
    logger = logging.getLogger()

    if chain_config is None:
        try:
            chain_config = get_env_variable("CHAIN_CONFIG_PATH")
        except ValueError:
            logger.error("Chain config path must be set via the commandline or environment")
            raise ValueError("Chain config path not set")

    if position_config is None:
        try:
            position_config = get_env_variable("POSITION_CONFIG_PATH")
        except ValueError:
            logger.error("Position config path must be set via the commandline or environment")
            raise ValueError("Position config path not set")

    set_chain_resource_config_path(chain_config)
    set_position_spec_config_path(position_config)
    create_position_reports()


if __name__ == '__main__':
    parser = ArgumentParser(
        prog="Uniswap Position Breakdowns",
        description="Utility for breaking down underlying tokens from Uniswap LP Positions at arbitrary block heights",
    )

    parser.add_argument('-c', '--chain-config', required=False,
                        help="Path to a chain resource config file. This can also be specified via the environment")
    parser.add_argument('-p', '--position-config', required=False,
                        help='Path to a position config file. This can also be specified via the environment')
    parser.add_argument('-v', '--verbose', action='count', default=0)

    args = parser.parse_args()
    main(**vars(args))
