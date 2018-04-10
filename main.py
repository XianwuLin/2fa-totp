#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request
from tinydb import Query, TinyDB
from crypt import AESCipher
import time
from totp import Totp
from expiringdict import ExpiringDict

app = Flask(__name__)
app.secret_key = '19#^f8kV8D55h!TXruYum%^VQh$zsCeQ'

DB = TinyDB('./db.json')
query = Query()

passphrase = "6V5#645L5FJn#Zc9i^i$b^3*38dShnk$"
aes = AESCipher(passphrase)

CACHE = ExpiringDict(max_len=10000, max_age_seconds=30)

def response(status, message, result=None):
    return jsonify({
        "status": status,
        "message": message,
        "result": result
    })

def response_success(result=None):
    return response(2000, "success", result)


@app.route('/api/create_seed', methods=['POST'])
def create_seed():
    """生成一个seed和对应的url"""
    username = request.form.get('username')
    tp = Totp()
    tp.create_seed()
    return response_success(result={"url": tp.create_url(username), "seed": tp.seed})


@app.route('/api/save_seed', methods=['POST'])
def save_seed():
    """提供用户名、seed和最近两次token，保存数据"""
    username = request.form.get('username')
    seed = request.form.get('seed')
    first_token = request.form.get("first_token")
    second_token = request.form.get("second_token")
    # first_token和second_token不能重复
    if first_token == second_token:
        return response(status=4000, message="verify seed fail")
    # 已存在的用户不允许再添加seed
    if DB.search(query.username == username):
        return response(status=4004, message="username exists")

    tp = Totp(seed=seed)
    if tp.seed_verify(second_token) and tp.seed_verify_last(first_token):
        # seed aes256加密
        seed_aes = aes.encrypt(seed)
        # 不允许出现两个一样的seed，提高安全性
        if DB.search(query.seed == seed_aes):
            return response(status=4001, message="seed repeat")
        # 保存到db
        DB.insert({'username': username, 'seed': seed_aes, 'created': int(time.time())})
        return response_success()
    else:
        return response(status=4000, message="verify seed fail")


@app.route('/api/verify_token', methods=['POST'])
def verify_token():
    """验证用户的token是否正确"""
    username = request.form.get('username')
    token = request.form.get("token")

    # 确保token只能使用一次
    if CACHE.get(token):
        return response(status=4003, message="token verify fail")
    else:
        CACHE[token] = 1

    # 如果用户不存在，抛出错误
    users = DB.search(query.username == username)
    if not users:
        return response(status=4002, message="username not exists")

    user = users[0]
    seed = aes.decrypt(user.get("seed"))
    tp = Totp(seed=seed)
    if tp.seed_verify(token):
        return response_success()
    else:
        return response(status=4003, message="token verify fail")


if __name__ == '__main__':
    app.run(port=8080)
