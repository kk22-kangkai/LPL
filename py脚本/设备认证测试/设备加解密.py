import base64
import json
from binascii import unhexlify, hexlify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests


base_url='https://api.snapmaker.cn/api'
base64_encoded_key = "NWEzNDBiODhjYTYyZWEzNDJiZWI3NjVkYmE4NTQ5NTk="
nonce=428170
username="lpl106464@gmail.com"
pw ='be029a15c4cc2b85c146e4b855fff665ea2a7c19267da576a019f0c9a33de683'
def aes_ecb_encrypt(key_bytes, plain_text):
    """
    使用 AES ECB 模式对明文进行加密，并返回 Base64 编码的密文。
    """
    try:
        # 创建 AES 加密器，模式为 ECB
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        # 对明文进行 PKCS7 填充并编码为字节
        padded_plain_text = pad(plain_text.encode('utf-8'), AES.block_size)
        # 执行加密
        encrypted_bytes = cipher.encrypt(padded_plain_text)
        # 将加密后的字节数据 Base64 编码为字符串
        base64_encoded_data = base64.b64encode(encrypted_bytes).decode('ascii')
        return base64_encoded_data
    except Exception as e:
        print(f"加密失败: {e}")
        return None
def get_bearer_auth_header(token):
    """生成 Bearer Authorization 请求头。"""
    return {"Authorization": f"Bearer {token}"}
def aes_ecb_decrypt(key_bytes, base64_encoded_data):
    """
    使用 AES ECB 模式对 Base64 编码的密文进行解密，并返回原始明文。
    """
    try:
        # Base64 解码密文
        encrypted_bytes = base64.b64decode(base64_encoded_data)
        # 创建 AES 解密器，模式为 ECB
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        # 执行解密，并移除填充
        decrypted_padded_bytes = cipher.decrypt(encrypted_bytes)
        decrypted_data = unpad(decrypted_padded_bytes, AES.block_size).decode('utf-8')
        return decrypted_data
    except Exception as e:
        print(f"解密失败: {e}")
        return None
def get_basic_auth_header(client_id, client_secret):
            """生成 Basic Authorization 请求头。"""
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json"
                    }
def user_login():
    url = f"{base_url}/oauth2/token"
    print(url)
    params = {
        "grant_type": "password",
        "username": username,
        "password":pw}
    headers = get_basic_auth_header('mall-app', '123456')
    rq = requests.post(url, params=params, headers=headers)
    data = json.loads(rq.text)
    token=data["data"]["access_token"]
    return token

def device_action(sn,sign):
    url = f"{base_url}/oauth2/token"
    params = {
        "grant_type": "snapmaker_device",
        "sign": sign,
        "scope": "mqtt",
        "sn": sn,
        "productCode": "LAVATEST123",
        "nonce": nonce,
        "refresh": "true"}
    headers = get_basic_auth_header('mall-app', '123456')

    re = requests.request("POST", url, params=params, headers=headers)
    return json.loads(re.text)
def device_post_code(sn,sign,operate):
    url = f"{base_url}/device/connect/auth"
    json_data = {
        "sign": sign,
        "sn": sn,
        "productCode": "LAVATEST123",
        "nonce": nonce,
        "operate": operate}
    rq = requests.request("POST", url, json=json_data)
    data=json.loads(rq.text)
    auth_code = data['data']['authCode']
    return auth_code
def bind_user_to_device(operate,nickname,authCode,token):
    url =f"{base_url}/device/connect/auth"
    json_data = {
        "nickname": nickname,
        "authCode": authCode,
        "operate": operate}
    headers = {
        "Content-Type": "application/json",
        **get_bearer_auth_header(token)  # 合并授权头
    }
    rq = requests.request("POST", url, json=json_data, headers=headers)
    return  json.loads(rq.text)
def search_device(token):
    url = f"{base_url}/device/list"
    headers = {
        "Content-Type": "application/json",
        **get_bearer_auth_header(token)  # 合并授权头
    }
    json_data = {
    "pageIndex": 1,
    "pageRows": 10
}

    rq = requests.request("POST", url, headers=headers ,json=json_data)
    return json.loads(rq.text)

