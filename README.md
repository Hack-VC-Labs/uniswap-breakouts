# uniswap-breakouts
Library and utility to help break out underlying token amounts from uniswap positions at arbitrary block hights

### Usage

clone the repo and install with pip:
`pip install .`

fill out chain resource and position config files like the examples in the `example_configs` directory. The source code can be used as a library or a command line tool from the `main.py` module

run the command line tool by pointing to the configs via the environment or on the commandline. 

You can specify an output file for the JSON position report via the command line. Use verbose mode (`-v`) to see more detail on the process. 

TODO:

 - [x] More Logging
 - [x] Option to export reports somewhere other than STDOUT
 - [ ] Prettier reports
 - [ ] Test
   - [x] Integration
   - [ ] Unit
 - [ ] Examples
 - [ ] Write out usage here
 - [x] Linting and Clean Up
