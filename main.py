import time
import requests
import execjs
import pytesseract
from lxml import etree
from urllib.parse import urlencode
from datetime import datetime
from PIL import Image
import numpy as np 
import matplotlib.pyplot as plt 


class UnifiedIdAuthLogin:
    def __init__(self, username, password, origin):
        self.username = username
        self.password = password
        self.origin = origin
        self.session = requests.session()
        self.session.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
            "Accept-Encoding": "gzip, deflate", 
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8", 
            "Host": origin.split('//')[1], 
            "Origin": origin, 
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        }
        self.form_data = dict()
        self.pwd_default_encryptSalt = ''
        self.retry_times = 10   # 登录错误次数

     # 登录主页
    def authserver_login(self):
        authserver_login_url = self.origin + "/authserver/login"
        res = self.session.get(authserver_login_url)

        tree = etree.HTML(res.text)
        self.form_data['username'] = self.username
        self.form_data['lt'] = tree.xpath('//*[@id="casLoginForm"]/input[1]/@value')[0]
        self.form_data['dllt'] = tree.xpath('//*[@id="casLoginForm"]/input[2]/@value')[0]
        self.form_data['execution'] = tree.xpath('//*[@id="casLoginForm"]/input[3]/@value')[0]
        self.form_data['_eventId'] = tree.xpath('//*[@id="casLoginForm"]/input[4]/@value')[0]
        self.form_data['rmShown'] = tree.xpath('//*[@id="casLoginForm"]/input[5]/@value')[0]
        self.pwd_default_encryptSalt = tree.xpath('//*[@id="pwdDefaultEncryptSalt"]/@value')[0]

    def get_captcha(self):
        params = {
            "username": self.username, 
            "pwdEncrypt2": "pwdEncryptSalt", 
            "timestamp": str(round(time.time() * 1000))
        }
        # 是否需要验证码
        needCaptcha_url = self.origin + "/authserver/needCaptcha.html?" + urlencode(params)
        res = self.session.get(needCaptcha_url)

        if res.text == 'true':
            ts = round(datetime.now().microsecond / 1000)  # get milliseconds
            captcha_url = self.origin + "/authserver/captcha.html?" + urlencode({"ts": ts})
            res = self.session.get(captcha_url)
            with open('captcha.jpg', mode='wb') as f:
                f.write(res.content)

            code = self.read_captcha()
            self.form_data['captchaResponse'] = code

    def read_captcha(self):
        img = Image.open('captcha.jpg').convert('L')
        img = np.array(img)
        height, width = img.shape[0], img.shape[1]
        threshold = 120
        for h in range(height):
            for w in range(width):
                if img[h][w] > threshold:
                    img[h][w] = 255
                else:
                    img[h][w] = 0
        im = Image.fromarray(img)
        if tesseract_cmd_path is not None:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
        code = pytesseract.image_to_string(im).strip().lower()

        return code

    def login(self): 
        # AES password
        with open('encrypt.js', mode='r') as f:
            ctx = execjs.compile(f.read())
            encrypt_pwd = ctx.call('encryptAES', self.password, self.pwd_default_encryptSalt)
        self.form_data['password'] = encrypt_pwd

        # login 
        login_url = self.origin + "/authserver/login"
        self.session.post(login_url, data=self.form_data)
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        if 'iPlanetDirectoryPro' not in cookies.keys() and self.retry_times:
            self.run()  # relogin, 暂时以登录后某一cookie判断是否登录成功
            self.retry_times = self.retry_times - 1
        else:
            return cookies

    def run(self):
        self.authserver_login()
        self.get_captcha()
        cookies = self.login()
        print(cookies)


if __name__ == '__main__':
    username = 'x'
    password = 'x'
    origin = 'http://id.fzu.edu.cn'
    # tesseract安装路径。如果已经添加到环境变量请留空
    tesseract_cmd_path = r"C:\Users\TempProgram\Tesserocr\tesseract.exe"
    UnifiedIdAuthLogin(username, password, origin).run()
