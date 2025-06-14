from 设备加解密 import *
from mqtt_connect import *
import functools

def  net_connect():
    # --- 1. 密钥准备 ---
    # 这是你的原始 Base64 编码的密钥字符串
    # Base64 解码得到十六进制密钥字符串 "5a340b88ca62ea342beb765dba854959"
    hex_key_bytes = base64.b64decode(base64_encoded_key)
    hex_key_string = hex_key_bytes.decode('ascii')
    actual_aes_key = unhexlify(hex_key_string)
    token = user_login()
    print(aes_ecb_encrypt(actual_aes_key, "B42275B5150EEA9A&productCode=LAVATEST123&operate=0&nonce=285861"))
    # print(aes_ecb_decrypt(actual_aes_key,"2Zdtbw0vBJfihP4NQdA3jyel9o9NP22/DVHUhiRXm9pDLkuHsWRac9FdFCycmQTdI2EKS7mE/XZINvpQ22LYYg=="))
    # 设备激活，绑定用户
    # for i in range(0, 11):
    #     plain_text_to_encrypt = f'{i}&productCode=LAVATEST123&nonce={nonce}'
    #     p_plain_text_to_encrypt = f'{i}&productCode=LAVATEST123&operate=0&nonce={nonce}'
    #     encrypted_base64_result = aes_ecb_encrypt(actual_aes_key, plain_text_to_encrypt)
    #     p_encrypted_base64_result = aes_ecb_encrypt(actual_aes_key, p_plain_text_to_encrypt)
    #     ac = device_action(i, encrypted_base64_result)
    #     authcode = device_post_code(i, p_encrypted_base64_result, 0)
    #     bind_user_to_device(0, '1', authcode, token)
    #     # 设备进行mqtt连接
    #     CONFIG = load_and_prepare_credentials(ac)
    #     connect(CONFIG)

def connect_lan_two_stage(broker_ip, accesscode, operational_callbacks=None, callback_args=None, ports=None):
    """
    执行一个两阶段的 MQTT 连接。此函数现在是一个纯粹的流程编排器。
    """
    ports = ports or {'mqtt': 1884, 'mqtts': 8883}
    # 创建一个仅在此次调用中有效的共享状态
    shared_state = {
        'certificates_received': False, 'temp_files': {}, 'client_id': None ,'sn':None

    }

    # ---- 阶段一：获取证书 ----
    print(f"--- [连接函数] 开始阶段一：获取pincode (pincode: {accesscode}) ---")
    ID="172.18.1.61"
    client_stage1 = mqtt.Client(client_id=ID)
    # 绑定外部定义的、用于第一阶段的回调
    client_stage1.on_connect = functools.partial(on_connect_handle_lan_1,accesscode,broker_ip )
    client_stage1.on_message = functools.partial(on_message_handle_lan_1,shared_state)

    try:
        client_stage1.connect(broker_ip, ports['mqtt'])
        client_stage1.loop_start()
        start_time = time.time()
        while not shared_state['certificates_received']:
            if time.time() - start_time > 30:
                client_stage1.loop_stop()
                print("❌ [连接函数] 获取证书超时！")
                return None,None
            time.sleep(0.5)
    except Exception as e:
        print(f"❌ [连接函数] 阶段一发生连接错误: {e}")
        return None,None

    if not shared_state['certificates_received']:
        print("😔 [连接函数] 未能获取证书，终止。")
        return None,None

    # ---- 阶段二：安全连接 ----
    print(f"\n--- [连接函数] 开始阶段二：安全连接 ---")
    temp_files = shared_state['temp_files']
    new_client_id = shared_state['client_id']
    client_stage2 = mqtt.Client(client_id=new_client_id)
    sn=shared_state['sn']
    # 绑定外部定义的、用于第二阶段的业务回调
    if operational_callbacks:
        # 检查是否需要绑定 on_connect
        if 'on_connect' in operational_callbacks:
            on_connect_handler = operational_callbacks['on_connect']
            # 我们明确知道 on_connect 需要 sn，所以为它单独创建 partial
            bound_handler = functools.partial(on_connect_handler, sn)
            client_stage2.on_connect = bound_handler

        # 检查是否需要绑定 on_message
        if 'on_message' in operational_callbacks:
            # on_message 不需要 sn，所以直接赋值
            client_stage2.on_message = operational_callbacks['on_message']

    try:
        client_stage2.tls_set(
            ca_certs=None,  # <-- 不再需要 CA 证书，可以设为 None 或直接移除此行
            certfile=temp_files['cert'],
            keyfile=temp_files['key'],
            # --- 关键改动 ---
            # 将 cert_reqs 设置为 ssl.CERT_NONE
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLS
        )
        client_stage2.connect(broker_ip, ports['mqtts'])
        client_stage2.loop_start()
        print("🎉 [连接函数] 两阶段连接成功！")
        return client_stage2,new_client_id,sn
    except Exception as e:
        print(f"❌ [连接函数] 阶段二发生错误: {e}")
        return None
    finally:
        # 确保临时文件被清理
        print("ℹ️ [连接函数] 清理临时证书文件...")
        for path in temp_files.values():
            if os.path.exists(path):
                os.remove(path)
        print("✅ [连接函数] 清理完成。")

if __name__ == "__main__":
  IP="172.18.0.85"
  ACCESS_CODE="46436858"
  my_app_callbacks = {
      'on_connect': on_connect,
      'on_message': simple_on_message
  }
  client,new_client_id,sn= connect_lan_two_stage(IP, ACCESS_CODE, my_app_callbacks)
  if client:
      print("\n====== 主程序：连接成功，应用进入监听状态... ======")
      print("你可以使用其他MQTT客户端向以下主题发布消息进行测试:")
      print(f"  - {sn}/config/request")
      try:
          while True:
              time.sleep(1)
      except KeyboardInterrupt:
          print("\n程序被中断，正在停止客户端...")
          client.loop_stop()
          client.disconnect()
          print("客户端已停止。")
  else:
      print("\n====== 主程序：连接流程失败，程序退出 ======")