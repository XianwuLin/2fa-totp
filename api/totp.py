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
        """生成种子"""
        self.seed = pyotp.random_base32(length=length)
        self.totp = pyotp.TOTP(self.seed)
        return self.seed

    def token_verify(self, token, jet_lag_unit=0, valid_window=1):
        """token校验"""
        return self.totp.verify(token,
                                for_time=datetime.datetime.now() + datetime.timedelta(seconds=30) * jet_lag_unit,
                                valid_window=valid_window)

    def calc_jet_lag_unit(self, first_token, second_token, max_units=30):
        """计算和本地的时差单元（1个时差单元30s），默认最大30*30s"""
        for unit in xrange(-max_units, max_units + 1):
            if self.token_verify(second_token, jet_lag_unit=unit, valid_window=0) and self.token_verify(first_token, jet_lag_unit=unit - 1, valid_window=0):
                return unit
        return None

    def create_url(self, account_name, app_name="Ttotp"):
        """生成扫描用的url"""
        return self.totp.provisioning_uri(name=account_name, issuer_name=app_name)


def main():
    tp = Totp()
    print tp.create_seed()
    print tp.create_url("abc")


if __name__ == '__main__':
    main()
