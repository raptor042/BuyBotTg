from web3 import Web3
import logging

from __web3__.config import PAIR_ERC20_ABI
from __db__.db import get_chats

def validateAddress(address: str) -> bool:
    if Web3.is_address(address) or Web3.is_checksum_address(address):
        return True
    else:
        return False
    
def name(web3, address: str) -> str:
    try:
        token = web3.eth.contract(address=address, abi=PAIR_ERC20_ABI["abi"])
        name = token.functions.name.call()

        print(name)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    else:
        return name
    
def supply(web3, address: str) -> str:
    try:
        token = web3.eth.contract(address=address, abi=PAIR_ERC20_ABI["abi"])
        supply = token.functions.totalSupply.call()

        print(supply)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    else:
        return supply

def getBuys(web3, db):
    chats = get_chats(db=db)
    print(chats)

    for chat in chats:
        address = chat["token"]
        print(address)
        try:
            token = web3.eth.contract(address=address, abi=PAIR_ERC20_ABI["abi"])
            print(token)
            logs = token.events.Transfer().get_logs(fromBlock="latest", toBlock="latest")
            print(f"logs: {logs}, length: {len(logs)}")

            for log in logs:
                print(f"{log["args"]["from"]} transferred {log["args"]["value"]} to {log["args"]["to"]}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")