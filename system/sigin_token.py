import time
from django.core import signing
import hashlib

# alg使用的算法
HEADER = {'typ': 'JWP', 'alg': 'default'}
TOKEN_KEY = 'nols'
TOKEN_SALT = 'xiaoxiao520'
TIME_OUT = 30 * 60


# 加密

class Token():


    def encrypt(self,obj):
        value = signing.dumps(obj, key=TOKEN_KEY, salt=TOKEN_SALT)
        value = signing.b64_encode(value.encode()).decode()
        return value

    # 解密
    def decrypt(self,src):
        src = signing.b64_decode(src.encode()).decode()
        raw = signing.loads(src, key=TOKEN_KEY, salt=TOKEN_SALT)
        print(type(raw))
        return raw


    # 生成token信息
    def create_token(self,username, password):
        # 1. 加密头信息
        header = self.encrypt(HEADER)
        # 2. 构造Payload
        payload = {
            "username": username,
            "password": password,
            "iat": time.time()
        }
        payload = self.encrypt(payload)
        # 3. 生成签名
        md5 = hashlib.md5()
        md5.update(("%s.%s" % (header, payload)).encode())
        signature = md5.hexdigest()
        token = "%s.%s.%s" % (header, payload, signature)
        # 4.存储到缓存中
        return token


    def get_payload(self,token):
        payload = str(token).split('.')[1]
        payload = self.decrypt(payload)
        return payload


    # 通过token获取用户名
    def get_username(self,token):
        payload = self.get_payload(token)
        return payload['username']
        pass



