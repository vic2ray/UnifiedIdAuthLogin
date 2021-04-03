# UnifiedIdAuthLogin
金智教育统一身份认证登录获取cookie

![image-20210403105546569](https://gitee.com/juaran/typora-image/raw/master/typora/image-20210403105546569.png)
统一登录地址：http://id.fzu.edu.cn/authserver/login

## 登录流程分析

### 1. 验证是否需要验证码

在输入框输入用户名后，触发请求：

> http://id.fzu.edu.cn/authserver/needCaptcha.html?username=xxx&pwdEncrypt2=pwdEncryptSalt&_=1617419933902
>
> true

返回true代表需要验证码，返回false代表不需要验证码。当尝试登录一次或几次失败时将触发验证，一般属于后端验证，前端无法绕过。

请求参数中包含`pwdEncrypt2=pwdEncryptSalt`，搜索pwdEncryptSalt定位到`login.js?v=1.0`文件：

``` javascript
var _t = username.val();  // 获取用户名
try{
    // AES加密，arg1=用户名，arg2=获取动态密码加密salt
    _t = encryptAES(_t,$("#casDynamicLoginForm").find("#dynamicPwdEncryptSalt").val());  
}catch(e){
}
```

查看js文件，其中包含`encryptAES.js`，直接调用进行加密。定位到网页元素`#pwdDefaultEncryptSalt`:

``` html
<input type="hidden" name="lt" value="LT-506399-2RS0W7HbXbGvLdU2oHx3n1xjeeAnj21617415016564-eM0e-cas">
<input type="hidden" name="dllt" value="dynamicLogin">
<input type="hidden" name="execution" value="e2s4">
<input type="hidden" name="_eventId" value="submit">
<input type="hidden" name="rmShown" value="1">
<input type="hidden" id="dynamicPwdEncryptSalt" value="xWicniCy1PKSfia7">
```

这几个字段均为隐藏表单元素，猜测在后面登录时用到。每次刷新页面动态生成这些value。

**PS**：后来发现`#dynamicPwdEncryptSalt`是用于“动态验证码登录”表单加密用的，而`#pwdDefaultEncryptSalt`才是“用户登录”表单用到的。

### 2. 获取验证码

验证码图片请求：

> http://id.fzu.edu.cn/authserver/captcha.html?ts=174

后面ts应该是随机数？不过没关系，在网页中同样可以找到，是动态生成的：

``` html
<img id="captchaImg" class="captcha-img" alt="验证码" title="验证码" src="captcha.html?ts=844">
```

搜索js文件找到`login-wisedu_v1.0.js?v=1.0`：

``` javascript
// 绑定换验证码的点击事件 
$("#casLoginForm").find("#changeCaptcha").bind("click", function () {
            $("#casLoginForm").find("#captchaImg").attr("src", "captcha.html?ts=" + new Date().getMilliseconds());
        });
```

发现`ts`是当前时间的毫秒数（0-999ms）。一张验证码如下所示：

![验证码](https://gitee.com/juaran/typora-image/raw/master/typora/captcha.html)

验证码中有很多背景噪声，可以使用tesserocr等神经网络框架进行识别。

### 3. 发起登录请求

> Request URL: http://id.fzu.edu.cn/authserver/login
> Request Method: POST
>
> username: xxx
> password:ivhgyjNGNWoHVBhUmlrXwMns8Vg81NMhZ%2FAl8RVs%2BNomMk7gP4ETOQf8Fwn7svB8fwa7yzJvhxmQS51XFP%2FbRAYrGXToe4yuLmwrbRScWGM%3D
> captchaResponse: aqe8
> lt: LT-506399-2RS0W7HbXbGvLdU2oHx3n1xjeeAnj21617415016564-eM0e-cas
> dllt: userNamePasswordLogin
> execution: e2s5
> _eventId: submit
> rmShown: 1

其中`password`做了加密处理，`captchaResponse`是输入验证码。POST表单后五个在隐藏表单域内可以找到。

搜索password关键词定位到发送登录请求的代码段(`login-wisedu_v1.0.js?v=1.0`)：

``` javascript
// 帐号登陆提交banding事件
var casLoginForm = $("#casLoginForm");
casLoginForm.submit(doLogin);
function doLogin() {
    var username = casLoginForm.find("#username");
    var password = casLoginForm.find("#password");
    var captchaResponse = casLoginForm.find("#captchaResponse");
	// ... 省略判空代码
    _etd2(password.val(),casLoginForm.find("#pwdDefaultEncryptSalt").val());
}
```

分别获取到了用户名、密码、验证码三个框框的输入，最后一步加密密码。第一参数是密码明文，第二参数是密码加密颜值（密钥K），与前面找到的`#dynamicPwdEncryptSalt`不同（不是同一个表单）。搜索网页可以找到：

``` html
<input type="hidden" id="pwdDefaultEncryptSalt" value="9NSeYHbjUn7df6Y5">
```

当前js文件内搜索`_estd2`找到一行代码展开后：

``` javascript
function _etd(_p0) {  // 这个加密函数好像没有用到
	try {
		var _p2 = encryptAES(_p0, pwdDefaultEncryptSalt);
		$("#casLoginForm").find("#passwordEncrypt").val(_p2);
	} catch(e) {
		$("#casLoginForm").find("#passwordEncrypt").val(_p0);
	}
} 
function _etd2(_p0, _p1) {  // 调用的是这个加密函数，参数分别是密码明文和加密salt
	try {
		var _p2 = encryptAES(_p0, _p1);
		$("#casLoginForm").find("#passwordEncrypt").val(_p2);
	} catch(e) {
		$("#casLoginForm").find("#passwordEncrypt").val(_p0);
	}
}
```

这个加密函数调用了encryptAES加密后，将值赋给了`#passwordEncrypt`这个元素，找一下发现：

``` html
<input id="password" placeholder="密码" class="auth_input" type="password" value="" autocomplete="off">
<input id="passwordEncrypt" name="password" style="display:none;" type="text" value="1">
<span id="passwordError" style="display:none;" class="auth_error">请输入密码</span>
```

第一个表单域是密码输入，第二个是加密密码表单域，`display:none`隐藏起来了，发起POST请求时获取的是这个值。

### 4. 总结

1. 当前登录请求是否需要验证码
2. 获取隐藏表单域`#pwdDefaultEncryptSalt`的值，进行`AES(password, salt)`加密得到密文
3. 获取其他隐藏表单域的值，发起登录请求

## Python模拟登录

### 1. 获取隐藏字段

使用HTTP请求库requests和解析库lxml，解析隐藏表单域的值。

``` python
import requests
from lxml import etree

username = "xxxx"
password = "xxxx"
session = requests.session()
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
    "Accept-Encoding": "gzip, deflate", 
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8", 
    "Host": "id.fzu.edu.cn", 
    "Origin": "http://id.fzu.edu.cn", 
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
}

# 登录主页
authserver_login_url = "http://id.fzu.edu.cn/authserver/login"
res = session.get(authserver_login_url, headers=headers)
tree = etree.HTML(res.text)
form_data = dict()
form_data['username'] = username
form_data['lt'] = tree.xpath('//*[@id="casLoginForm"]/input[1]/@value')[0]
form_data['dllt'] = tree.xpath('//*[@id="casLoginForm"]/input[2]/@value')[0]
form_data['execution'] = tree.xpath('//*[@id="casLoginForm"]/input[3]/@value')[0]
form_data['_eventId'] = tree.xpath('//*[@id="casLoginForm"]/input[4]/@value')[0]
form_data['rmShown'] = tree.xpath('//*[@id="casLoginForm"]/input[5]/@value')[0]
pwd_default_encryptSalt = tree.xpath('//*[@id="pwdDefaultEncryptSalt"]/@value')[0]
```

### 2. 获取验证码

请求验证码，如果返回false则不需要添加表单字段，否则请求验证码并识别，添加验证码表单字段。

``` python
from urllib.parse import urlencode
from datetime import datetime

timestamp = str(round(time.time() * 1000))
params = {
    "username": username, 
    "pwdEncrypt2": "pwdEncryptSalt", 
    "timestamp": timestamp
}
# 是否需要验证码
needCaptcha_url = "http://id.fzu.edu.cn/authserver/needCaptcha.html?" + urlencode(params)
res = session.get(needCaptcha_url, headers=headers)
if res.text == 'true':
    ts = round(datetime.now().microsecond / 1000)  # get milliseconds
    captcha_url = "http://id.fzu.edu.cn/authserver/captcha.html?" + urlencode({"ts": ts})
    res = session.get(captcha_url, headers=headers)
    with open('captcha.png', mode='wb') as f:
        f.write(res.content)
    form_data['captchaResponse'] = input()
```

PS：这里手动输入验证码~~. 后面可以替换为验证码识别接口调用。

### 3. 模拟登陆

安装pyexecjs库进行AES加密。在console中调用encryptAES发现其加密结果为108位，

``` python
# AES password
import execjs

with open('encrypt.js', mode='r') as f:
    ctx = execjs.compile(f.read())
    encrypt_pwd = ctx.call('encryptAES', password, pwd_default_encryptSalt)
form_data['password'] = encrypt_pwd

# login 
login_url = "http://id.fzu.edu.cn/authserver/login"
res = session.post(login_url, headers=headers, data=form_data)
# print(res.text)  # 登录后自动跳转页面内容

requests.utils.dict_from_cookiejar(session.cookies)
```

> {
> 'iPlanetDirectoryPro':'AQIC5wM2LY4Sfcx486iwX4F%2BGMxutOP%2FprhoWzJcS%2FledKo%3D%40AAJTSQACMDE%3D%23',
> 'JSESSIONID_auth': 'gdqWjJ_vOsVUEq-MJayGuSj2675NiJ2ORJlEr2NQAJgYitiEjo-Z!1673517085',
>  'route': '31b1acb26967d981571bca691c13c483',
>  'CASTGC': 'TGT-51442-AE7gZhhfdF1y1YYwpNIHUbFFu3NzhMweMeSdqffxXztxWBcf2w1617434050431-KVIm-cas'
>
> }

至此，成功获取到登录后Cookies信息。

## 验证码识别

用到Python的图像处理库pillow，数值分析库numpy，绘图库matplotlib，光学符号识别库pytesseract。

思路是先将验证码转为灰度图，再转换为ndarray的二维数组，删除背景噪声像素（与文字像素相比值更大，颜色更浅偏白）

``` python
from PIL import Image

img = Image.open('captcha2.jpg')
img = img.convert('L')

import numpy as np 
import matplotlib.pyplot as plt 

img = np.array(img)
plt.imshow(img, cmap='gray')
```

![image-20210403191739099](https://gitee.com/juaran/typora-image/raw/master/typora/image-20210403191739099.png)

遍历像素，将超过灰度值超过120的置为255，即白色；灰度值低于120的置为0，即黑色：

``` python
height = img.shape[0]
width = img.shape[1]
threshold = 120  # 像素阈值
for h in range(height):
    for w in range(width):
        if img[h][w] > threshold:
            img[h][w] = 255
        else:
            imgp[h][w] = 0
plt.imshow(img, cmap='gray')
```

![](https://gitee.com/juaran/typora-image/raw/master/typora/image-20210403210530113.png)

效果看起来不错，存在锯齿现象，但问题不大。

在使用pyteserract前需要先安装好tesseract，其带有识别程序和文字数据，自带有eng.traindata代表英文数字识别数据包。在使用前先设置可执行teserract的安装路径。

``` python
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\TempProgram\Tesserocr\tesseract.exe"
pytesseract.image_to_string(im).strip().lower()
```

> 'z2zh'

能准确识别出Z和2，下载几张新的图片均能够准确识别。看来这验证码难度不大，不需要再做CNN神经网络训练任务。

将以上验证码处理识别程序和前面的模拟登录结合，唯一的遗憾是整个Python程序外还需要安装tesseract软件。
