import requests
import json
import base64
import time
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad
import os
import string
import random
# --- 配置数据 (直接来自你提供的 JSON) ---
CONFIG = {
    "dev": {
        "domain": "http://pre.id.snapmaker.com",
        "gatewayPort": '',
        "client": "mall-app",
        "client_password": "123456",
        "user_param": {
            "username": "xyliu_leo@163.com",
            "password": "9c7d8a1fbd40678f91974115468582909108675f6ab310b0db381b4b324ca914"
        },
        "grant_type": {
            "password": "password",
            "sms": "urn:ietf:params:oauth:grant-type:sms_code",
            "email": "urn:ietf:params:oauth:grant-type:email",
            "device": "snapmaker_device",
            "refresh_token": "refresh_token"
        },
        "device_param": {
            "scope": "mqtt profile openid",
            "productCode": "LAVATEST123",
            "sn": "SNlavatest123",
            "codeLoginSign": "dD1+TRZ7oBZ2H2H7G7E8i5xsxZh4TFa+5U0N3lEXZY3P3Q0PILLDJce3tIxWcG80",
            "deviceId": "1", # 注意：这个deviceId在device login的GET请求里用到了，但POST请求里没有，看你实际API是哪个
            "idLoginSign": "", # 这个在你的请求示例里没有用到
            "authSign": "5a340b88ca62ea342beb765dba854959",
            "nonce": 123456 # 注意：nonce通常每次请求都应该是新的，这里只是个示例值。
        }
    }
}

# 提取常用配置
ENV_CONFIG = CONFIG["dev"]
DOMAIN = ENV_CONFIG["domain"]
GATEWAY_PORT = ENV_CONFIG["gatewayPort"]
CLIENT_ID = ENV_CONFIG["client"]
CLIENT_SECRET = ENV_CONFIG["client_password"]
USER_USERNAME = ENV_CONFIG["user_param"]["username"]
USER_PASSWORD = ENV_CONFIG["user_param"]["password"] # 密码可能需要加密或哈希处理
DEVICE_PRODUCT_CODE = ENV_CONFIG["device_param"]["productCode"]
DEVICE_SN = ENV_CONFIG["device_param"]["sn"]
DEVICE_CODE_LOGIN_SIGN = ENV_CONFIG["device_param"]["codeLoginSign"]
DEVICE_AUTH_SIGN = ENV_CONFIG["device_param"]["authSign"]
GRANT_TYPE_PASSWORD = ENV_CONFIG["grant_type"]["password"]
GRANT_TYPE_DEVICE = ENV_CONFIG["grant_type"]["device"]
NONCE = ENV_CONFIG["device_param"]["nonce"]

# API 基础 URL
BASE_URL = f"{DOMAIN}/api"

# --- 辅助函数 ---
def encrypt_device_data_aes(
    aes_key: str,          # AES 密钥 (bytes 类型，长度为 16, 24 或 32 字节)
    sn: str,                 # 设备的 SN 字符串
    product_code: str,
    nonce : str,
    operate: int = 0 ,
        # 操作类型 (默认为 0)
) -> tuple[str, str]:
    """
    使用 AES CBC 模式加密设备相关数据。

    加密的原始字符串格式为: "SN&productCode=<productCode>&operate=<operate>&nonce=<6位随机数>"

    Args:
        aes_key: 用于加密的 AES 密钥，必须是 bytes 类型，长度为 16 (AES-128),
                 24 (AES-192) 或 32 (AES-256) 字节。
        sn: 设备的序列号 (string)。
        product_code: 产品代码 (string)。
        operate: 操作类型 (int)，默认为 0。

    Returns:
        一个包含两个 Base64 编码字符串的元组 (iv_b64, ciphertext_b64)。
        iv_b64: 初始化向量 (IV) 的 Base64 编码字符串。
        ciphertext_b64: 加密后的密文的 Base64 编码字符串。

    Raises:
        ValueError: 如果 aes_key 长度不符合 AES 要求。
    """
    # 检查密钥长度
    aes_key= base64.b64decode(aes_key)
    if len(aes_key) not in (16, 24, 32):
        raise ValueError("AES 密钥长度必须为 16, 24 或 32 字节。")

    # 1. 生成 6 位随机数 Nonce
    dynamic_nonce = nonce

    # 2. 构建待加密的原始字符串
    # 严格按照 "SN&productCode=123456&operate=0&nonce=6位随机数" 格式
    raw_string_to_encrypt = (
        f"{sn}&productCode={product_code}&operate={operate}&nonce={dynamic_nonce}"
    )

    # 3. 将字符串编码为字节串
    plaintext_bytes = raw_string_to_encrypt.encode('utf-8')

    # 4. 初始化 AES 加密器 (CBC 模式)
    cipher = AES.new(aes_key, AES.MODE_CBC)
    iv = cipher.iv  # AES.new() 在 CBC 模式下会自动生成一个随机 IV

    # 5. 对明文进行 PKCS7 填充并加密
    padded_plaintext = pad(plaintext_bytes, AES.block_size)
    ciphertext = cipher.encrypt(padded_plaintext)

    # 6. 将 IV 和密文编码为 Base64 字符串
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')


    return iv_b64, ciphertext_b64

def get_basic_auth_header(client_id, client_secret):
    """生成 Basic Authorization 请求头。"""
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}

def get_bearer_auth_header(token):
    """生成 Bearer Authorization 请求头。"""
    return {"Authorization": f"Bearer {token}"}

def generate_dynamic_nonce(length=6):
    """生成一个时间戳作为 Nonce。在生产环境中，请使用更安全的随机字符串。"""
    characters = string.digits
    return ''.join(random.choice(characters) for i in range(length))

def make_request(method, url, headers=None, params=None, json_data=None):
    """通用 HTTP 请求函数。"""
    print(f"\n--- 发送 {method} 请求到: {url} ---")
    print(f"请求头: {headers}")
    if params:
        print(f"请求参数 (Query Params): {params}")
    if json_data:
        print(f"请求体 (JSON Body): {json.dumps(json_data, indent=2)}")

    try:
        response = requests.request(method, url, headers=headers, params=params, json=json_data)
        response.raise_for_status() # 对于 4xx 或 5xx 响应抛出 HTTPError
        print(f"响应状态码: {response.status_code}")
        try:
            response_json = response.json()
            print(f"响应 JSON: {json.dumps(response_json, indent=2)}")
            return response_json
        except json.JSONDecodeError:
            print(f"响应内容 (非 JSON): {response.text}")
            return response.text
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误: {e}")
        print(f"响应文本: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"请求超时: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"发生未知错误: {e}")
        return None

# --- API 端点函数 ---

def user_login():
    """用户登录以获取访问令牌。"""
    url = f"{BASE_URL}/oauth2/token"
    params = {
        "grant_type": GRANT_TYPE_PASSWORD,
        "username": USER_USERNAME,
        "password": USER_PASSWORD
    }
    headers = get_basic_auth_header(CLIENT_ID, CLIENT_SECRET)
    return make_request("POST", url, headers=headers, params=params)

def device_login(refresh=False):
    """
    设备登录以获取访问令牌。
    refresh=True 表示刷新现有令牌。
    """
    url = f"{BASE_URL}/oauth2/token"
    # 每次请求生成新的 Nonce
    current_nonce = generate_dynamic_nonce()

    params = {
        "grant_type": GRANT_TYPE_DEVICE,
        "productCode": DEVICE_PRODUCT_CODE,
        "sn": DEVICE_SN,
        "sign": encrypt_device_data_aes( DEVICE_AUTH_SIGN,DEVICE_SN,DEVICE_PRODUCT_CODE,current_nonce)[1],
        "nonce": current_nonce # 使用动态生成的 Nonce
    }
    if refresh:
        params["refresh"] = "true"

    headers = get_basic_auth_header(CLIENT_ID, CLIENT_SECRET)
    return make_request("POST", url, headers=headers, params=params)

def device_auth():
    """执行设备连接认证。"""
    url = f"{BASE_URL}/device/connect/auth"
    headers = {"Content-Type": "application/json"}
    # 每次请求生成新的 Nonce
    current_nonce = generate_dynamic_nonce()

    json_data = {
        "operate": 0,
        "productCode": DEVICE_PRODUCT_CODE,
        "sn": DEVICE_SN,
        "nonce": current_nonce, # 使用动态生成的 Nonce
        "sign": DEVICE_AUTH_SIGN
    }
    return make_request("POST", url, headers=headers, json_data=json_data)

def user_auth(access_token):
    """
    执行用户认证（可能用于设备绑定或其他用户操作）。
    需要一个有效的 Bearer 令牌。
    """
    url = f"{BASE_URL}/device/connect/auth"
    headers = {
        "Content-Type": "application/json",
        **get_bearer_auth_header(access_token) # 合并授权头
    }
    json_data = {
        "operate": 0,
        "nickname": "aaaa", # 你提供的示例中的昵称
        "authCode": "c99eO-6d" # 你提供的示例中的认证码
    }
    return make_request("POST", url, headers=headers, json_data=json_data)

def user_get_mqtt_secret(access_token):
    """
    获取用户的 MQTT 密钥。
    需要一个有效的 Bearer 令牌。
    """
    url = f"{BASE_URL}/device/getMqttCert"
    headers = get_bearer_auth_header(access_token)
    return make_request("GET", url, headers=headers)

# --- 示例用法 ---

if __name__ == "__main__":
    # 请确保你的网络环境可以访问到 http://localhost:8100

    # --- 步骤 1: 用户登录 ---
    print("\n========== 开始用户登录 ==========")
    user_token_response = user_login()
    user_access_token = None
    if user_token_response and 'access_token' in user_token_response:
        user_access_token = user_token_response['access_token']
        print(f"\n用户访问令牌已获取: {user_access_token}")
    else:
        print("\n用户登录失败。无法执行依赖用户令牌的操作。")

    # --- 步骤 2: 设备登录 ---
    print("\n========== 开始设备登录 ==========")
    # 注意：如果设备首次登录，refresh=False；如果刷新令牌，则设置 refresh`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````=True
    device_token_response = device_login(refresh=False)
    device_access_token = None
    if device_token_response and 'access_token' in device_token_response:
        device_access_token = device_token_response['access_token']
        print(f"\n设备访问令牌已获取: {device_access_token}")
    else:
        print("\n设备登录失败。")

    # --- 步骤 3: 设备认证 ---
    print("\n========== 开始设备认证 ==========")
    device_auth_response = device_auth()
    if device_auth_response:
        print("\n设备认证成功。")
    else:
        print("\n设备认证失败。")

    # --- 步骤 4: 用户认证 (需要先成功获取用户访问令牌) ---
    if user_access_token:
        print("\n========== 开始用户认证 ==========")
        user_auth_response = user_auth(user_access_token)
        if user_auth_response:
            print("\n用户认证成功。")
        else:
            print("\n用户认证失败。")
    else:
        print("\n跳过用户认证：用户访问令牌不可用。")

    # --- 步骤 5: 用户获取 MQTT 密钥 (需要先成功获取用户访问令牌) ---
    if user_access_token:
        print("\n========== 开始用户获取 MQTT 密钥 ==========")
        mqtt_secret_response = user_get_mqtt_secret(user_access_token)
        if mqtt_secret_response:
            print("\n用户获取 MQTT 密钥成功。")
        else:
            print("\n用户获取 MQTT 密钥失败。")
    else:
        print("\n跳过用户获取 MQTT 密钥：用户访问令牌不可用。")