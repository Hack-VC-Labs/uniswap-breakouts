# uniswap-breakouts
Library and utility to help break out underlying token amounts from uniswap positions at arbitrary block hights

### Usage

clone the repo and install with pip:
`pip install .`

fill out chain resource and position config files like the examples in the `example_configs` directory. The source code can be used as a library or a command line tool from the `main.py` module

run the command line tool by pointing to the configs via the environment or on the commandline. 

You can specify an output file for the JSON position report via the command line. Use verbose mode (`-v`) to see more detail on the process. 

```commandline
options:
  -h, --help            show this help message and exit
  -c CHAIN_CONFIG, --chain-config CHAIN_CONFIG
                        Path to a chain resource config file. This can also be specified via the environment
  -p POSITION_CONFIG, --position-config POSITION_CONFIG
                        Path to a position config file. This can also be specified via the environment
  -o OUT_FILE, --out-file OUT_FILE
                        If specified, reports will be output to path specified rather than the default STDOUT
  -v, --verbose
```


TODO:

 - [x] More Logging
 - [x] Option to export reports somewhere other than STDOUT
 - [ ] Test
   - [x] Integration
   - [ ] Unit
 - [x] Examples
 - [x] Linting and Clean Up
