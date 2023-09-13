from argparse import ArgumentParser
import logging
from typing import Optional

from uniswap_breakouts.config.load import set_chain_resource_config_path, set_position_spec_config_path
from uniswap_breakouts.report.report_runner import create_position_reports


def main(
    verbose: int,
    chain_config: Optional[str] = None,
    position_config: Optional[str] = None,
    out_file: Optional[str] = None,
) -> None:
    log_verbosity = [logging.ERROR, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=log_verbosity[verbose]
    )

    if chain_config is not None:
        set_chain_resource_config_path(chain_config)
    if position_config is not None:
        set_position_spec_config_path(position_config)

    create_position_reports(out_file)


if __name__ == '__main__':
    parser = ArgumentParser(
        prog="Uniswap Position Breakdowns",
        description="Utility for breaking down underlying tokens from Uniswap LP Positions",
    )

    parser.add_argument(
        '-c',
        '--chain-config',
        required=False,
        help="Path to a chain resource config file. This can also be specified via the environment",
    )
    parser.add_argument(
        '-p',
        '--position-config',
        required=False,
        help='Path to a position config file. This can also be specified via the environment',
    )
    parser.add_argument(
        '-o',
        '--out-file',
        required=False,
        help='If specified, reports will be output to path specified rather than the default STDOUT',
    )
    parser.add_argument('-v', '--verbose', action='count', default=0)

    args = parser.parse_args()
    main(**vars(args))
