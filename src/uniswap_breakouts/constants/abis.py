import json
from pathlib import Path

token_abi_path = Path(__file__).parent / 'token_contract_abi.json'
with open(token_abi_path) as abi_file:
    TOKEN_CONTRACT_ABI = json.load(abi_file)
