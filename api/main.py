#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request
from tinydb import Query, TinyDB
from crypt import AESCipher, bcrypt_checkpw, bcrypt_encrypt
import time
from totp import Totp
from expiringdict import ExpiringDict

app = Flask(__name__)
app.secret_key = '19#^f8kV8D55h!TXruYum%^VQh$zsCeQ'

DB = TinyDB('./db.json')
query = Query()

passphrase = "6V5#645L5FJn#Zc9i^i$b^3*38dShnk$"
aes = AESCipher(passphrase)

CACHE = ExpiringDict(max_len=10000, max_age_seconds=60)

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
    pin = request.form.get('pin')
    first_token = request.form.get("first_token")
    second_token = request.form.get("second_token")
    # first_token和second_token不能重复
    if first_token == second_token:
        return response(status=4000, message="verify seed fail")
    # 已存在的用户不允许再添加seed
    if DB.search(query.username == username):
        return response(status=4004, message="username exists")

    tp = Totp(seed=seed)
    # 计算服务器和本地的时间差
    jet_lag_unit = tp.calc_jet_lag_unit(first_token, second_token)
    if jet_lag_unit is None:
        # 如果超过了允许的时间差，则验证不通过
        return response(status=4000, message="verify seed fail")
    else:
        # seed aes256加密
        seed_aes = aes.encrypt(seed)
        # 不允许出现两个一样的seed，提高安全性
        if DB.search(query.seed == seed_aes):
            return response(status=4001, message="seed repeat")
        # 保存到db
        DB.insert({'username': username, 'seed': seed_aes, 'created': int(time.time()), "jet_lag_unit": jet_lag_unit, "pin": bcrypt_encrypt(pin)})
        return response_success()


@app.route('/api/resync', methods=['POST'])
def resync():
    """时间同步"""
    username = request.form.get('username')
    first_token = request.form.get("first_token")
    second_token = request.form.get("second_token")
    # first_token和second_token不能重复
    if first_token == second_token:
        return response(status=4000, message="verify seed fail")
    # 获取当前用户
    users = DB.search(query.username == username)
    if not users:
        return response(status=4002, message="username not exists")

    user = users[0]
    seed = aes.decrypt(user.get("seed"))
    tp = Totp(seed=seed)
    # 计算服务器和本地的时间差
    jet_lag_unit = tp.calc_jet_lag_unit(first_token, second_token)
    if jet_lag_unit is None:
        # 如果超过了允许的时间差，则验证不通过
        return response(status=4000, message="verify seed fail")
    else:
        # 更新时间差
        DB.update({'jet_lag_unit': jet_lag_unit}, query.username == username)
        return response_success()

@app.route('/api/verify_token', methods=['POST'])
def verify_token():
    """验证用户的token是否正确"""
    username = request.form.get('username')
    ptoken = request.form.get("ptoken")

    pin = ptoken[:-6]
    token = ptoken[-6:]

    # 如果用户不存在，抛出错误
    users = DB.search(query.username == username)
    if not users:
        return response(status=4002, message="username not exists")

    user = users[0]
    seed = aes.decrypt(user.get("seed"))
    jet_lag_unit = user.get("jet_lag_unit", 0)
    pin_hashed = user.get("pin")
    tp = Totp(seed=seed)
    if tp.token_verify(token, jet_lag_unit=jet_lag_unit) and bcrypt_checkpw(pin, pin_hashed):
        # 确保token只能被成功使用一次
        if CACHE.get(token):
            return response(status=4003, message="token verify fail")
        else:
            CACHE[token] = 1
        return response_success()
    else:
        return response(status=4003, message="token verify fail")


if __name__ == '__main__':
    app.run(port=8080)
