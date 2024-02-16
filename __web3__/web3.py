from web3 import Web3

def validateAddress(address: str) -> bool:
    if Web3.is_address(address) or Web3.is_checksum_address(address):
        return True
    else:
        return False