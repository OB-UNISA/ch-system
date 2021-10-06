import secrets
import os
import utils

from replit import db

key = os.getenv('KEY')


def create(user_id):
    api_keys = get_all()
    if user_id not in api_keys:
        api_key = secrets.token_hex(4)
        api_keys[user_id] = api_key
        db[key] = api_keys
        return api_key
    return None


def delete(user_id):
    api_keys = get_all()
    if user_id in api_keys:
        for boss in utils.BOSSES:
            utils.remove_sub(boss, user_id)
        del api_keys[user_id]
        db[key] = api_keys
        return True
    return False


def edit_userid(user_id, new_user_id):
    api_keys = get_all()
    if user_id in api_keys:
        api_keys[new_user_id] = api_keys.pop(user_id)
        return True
    return False


def validate_apikey(user_id, apikey):
    api_keys = get_all()
    if user_id in api_keys and api_keys[user_id] == apikey:
        return True
    return False


def get(user_id):
    return db[key][user_id]


def get_all():
    return db[key]


def get_users():
    return list(dict(db[key]).keys())


def delete_all():
    del db[key]
