import pyotp
import datetime


class Totp_pw(object):

    def __init__(self, pw=None):
        if pw is not None:
            self.pw = pw
            self.totp = pyotp.TOTP(pw)
        else:
            self.pw = None
            self.totp = None

    def create_pw(self, length=32):
        self.pw = pyotp.random_base32(length=length)
        self.totp = pyotp.TOTP(self.pw)
        return self.pw

    def pw_verify(self, token):
        return self.totp.verify(token, valid_window=1)

    def pw_verify_last(self, token):
        return self.totp.verify(token,
                        for_time=datetime.datetime.now() - datetime.timedelta(seconds=30),
                        valid_window=1)

    def create_url(self, account_name, app_name="Ttotp"):
        return self.totp.provisioning_uri(name=account_name, issuer_name=app_name)

    def create_qrcode(self, account_name, app_name="Ttotp"):
        import qrcode
        import base64
        import cStringIO
        url = self.create_url(account_name=account_name, app_name="Ttotp")
        qr = qrcode.QRCode(version=1,
                               error_correction=qrcode.constants.ERROR_CORRECT_L,
                               box_size=8,
                               border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        io_buffer = cStringIO.StringIO()
        img.save(io_buffer, format="JPEG")
        return base64.b64encode(io_buffer.getvalue())

def main():
    tp = Totp_pw()
    print tp.create_pw()
    with open("1.html", "w") as f:
        f.write('<img src="data:image/jpeg;base64,{0}" style="height: 180px">'.format(tp.create_qrcode(account_name="user")))
    print "finish"

if __name__ == '__main__':
    main()
