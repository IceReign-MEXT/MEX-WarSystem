from web3 import Web3
import base58 # <-- This should be here
import re

# ... rest of the code as provided in the previous fix for validators.py ...
def is_valid_sol_address(address: str) -> bool:
    """
    Checks if an address is a valid Solana address using base58 decoding.
    """
    if not isinstance(address, str):
        return False
    if not (32 <= len(address) <= 44):
        return False
    try:
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except ValueError:
        return False
# ... rest of the file ...
