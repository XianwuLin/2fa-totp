#!/usr/bin/python
# -*- coding: utf-8 -*-

import pyotp
import datetime


class Totp(object):

    def __init__(self, seed=None):
        if seed is not None:
            self.seed = seed
            self.totp = pyotp.TOTP(seed)
        else:
            self.seed = None
            self.totp = None

    def create_seed(self, length=32):
        self.seed = pyotp.random_base32(length=length)
        self.totp = pyotp.TOTP(self.seed)
        return self.seed

    def seed_verify(self, token):
        return self.totp.verify(token, valid_window=1)

    def seed_verify_last(self, token):
        return self.totp.verify(token,
                        for_time=datetime.datetime.now() - datetime.timedelta(seconds=30),
                        valid_window=1)

    def create_url(self, account_name, app_name="Ttotp"):
        return self.totp.provisioning_uri(name=account_name, issuer_name=app_name)

def main():
    tp = Totp()
    print tp.create_seed()
    print tp.create_url("abc")

if __name__ == '__main__':
    main()
