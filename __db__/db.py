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
    
def get_comps(db) -> dict:
    try:
        comp = db["comps"].find()
    except TimeoutError:
        logging.error("Cannot get comp data to database, may be due to poor network connectivity")
    else:
        return comp

def get_comp(db, query : dict) -> dict:
    try:
        comp = db["comps"].find_one(query)
    except TimeoutError:
        logging.error("Cannot get comp data to database, may be due to poor network connectivity")
    else:
        return comp

def set_comp(db, value : dict) -> dict:
    try:
        comp = db["comps"].insert_one(value)
    except TimeoutError:
        logging.error("Cannot post comp data to database, may be due to poor network connectivity")
    else:
        return comp

def update_comp(db, query: dict, value: dict) -> dict:
    try:
        comp = db["comps"].update_one(query, value)
    except TimeoutError:
        logging.error("Cannot update comp data to database, may be due to poor network connectivity")
    else:
        return comp
    
def delete_comp(db, query: dict) -> dict:
    try:
        comp = db["comps"].delete_one(query)
    except TimeoutError:
        logging.error("Cannot delete comp data to database, may be due to poor network connectivity")
    else:
        return comp