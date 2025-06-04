import base64
from binascii import unhexlify, hexlify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

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

if __name__ == "__main__":
    # --- 1. 密钥准备 ---
    # 这是你的原始 Base64 编码的密钥字符串
    base64_encoded_key = "NWEzNDBiODhjYTYyZWEzNDJiZWI3NjVkYmE4NTQ5NTk="

    # Base64 解码得到十六进制密钥字符串 "5a340b88ca62ea342beb765dba854959"
    hex_key_bytes = base64.b64decode(base64_encoded_key)
    hex_key_string = hex_key_bytes.decode('ascii')

    # 十六进制解码得到真正的 AES 二进制密钥（16 字节，128 位）
    actual_aes_key = unhexlify(hex_key_string)

    print(f"原始 Base64 密钥: {base64_encoded_key}")
    print(f"解码后的十六进制密钥字符串: {hex_key_string}")
    print(f"实际 AES 密钥字节长度: {len(actual_aes_key)} bytes")
    print("------------------------------------")

    # --- 2. 加密过程 ---
    plain_text_to_encrypt = "SNlavatest123&productCode=LAVATEST123&nonce=232143"
    print(f"待加密明文: {plain_text_to_encrypt}")

    encrypted_base64_result = aes_ecb_encrypt(actual_aes_key, plain_text_to_encrypt)
    if encrypted_base64_result:
        print(f"加密后的 Base64 密文: {encrypted_base64_result}")
    print("------------------------------------")

    # --- 3. 解密过程 ---
    # 使用之前加密得到的密文进行解密
    if encrypted_base64_result:
        decrypted_result = aes_ecb_decrypt(actual_aes_key, encrypted_base64_result)
        if decrypted_result:
            print(f"解密后的明文: {decrypted_result}")

            # --- 4. 验证 ---
            is_match = (plain_text_to_encrypt == decrypted_result)
            print(f"明文与解密结果是否匹配: {'✅ 匹配' if is_match else '❌ 不匹配'}")