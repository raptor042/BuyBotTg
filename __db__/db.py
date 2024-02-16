from pymongo import MongoClient
import certifi

import logging

def connect_db(uri : str):
    try:
        client = MongoClient(uri, tlsCAFile=certifi.where())
        db = client["BuyBot"]
    except TimeoutError:
        logging.error("Cannot connect to database, may be due to poor network connectivity")
        connect_db(uri=uri)
    else:
        return db
    
def get_chats(db) -> dict:
    try:
        chat = db["chats"].find()
    except TimeoutError:
        logging.error("Cannot get chat data to database, may be due to poor network connectivity")
    else:
        return chat

def get_chat(db, query : dict) -> dict:
    try:
        chat = db["chats"].find_one(query)
    except TimeoutError:
        logging.error("Cannot get chat data to database, may be due to poor network connectivity")
    else:
        return chat

def set_chat(db, value : dict) -> dict:
    try:
        chat = db["chats"].insert_one(value)
    except TimeoutError:
        logging.error("Cannot post chat data to database, may be due to poor network connectivity")
    else:
        return chat

def update_chat(db, query: dict, value: dict) -> dict:
    try:
        chat = db["chats"].update_one(query, value)
    except TimeoutError:
        logging.error("Cannot update chat data to database, may be due to poor network connectivity")
    else:
        return chat
    
def delete_chat(db, query: dict) -> dict:
    try:
        chat = db["chats"].delete_one(query)
    except TimeoutError:
        logging.error("Cannot delete chat data to database, may be due to poor network connectivity")
    else:
        return chat