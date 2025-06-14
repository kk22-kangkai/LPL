import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import tempfile
# --- 全局变量，用于存储从JSON中解析出的配置 ---
CONFIG = {}
PUBLISH_TOPICS = []
SUBSCRIBE_TOPICS = []


# --- MQTT 回调函数 ---

def on_connect(sn ,client, userdata,flags,rc):
    """
    连接成功后，执行核心的订阅和发布测试。
    """
    if rc == 0:
        print(f"✅ [设备 {'clientId'}] 连接成功!")
        # 1. 订阅所有指定主题
        print("\n🚀 开始订阅主题...")

        topic = f"{sn}/response"
        topic1 = f"{sn}/request"
        client.subscribe(topic, qos=1)
        print(f"  -> 已订阅: {topic}")
        # 2. 向所有指定主题发布一条测试消息
        print("\n🚀 开始发布消息...")
        test_message ={
    "jsonrpc": "2.0",
    "method": "machine.system_info",
    "id": 4665
    }
        test_message = json.dumps(test_message)
        client.publish(topic1, test_message, qos=1)
        print(f"  -> 已向主题 '{topic1}' 发布消息: '{test_message}'")

    else:
        print(f"❌ [设备 {'clientId'}] 连接失败，返回码: {rc}")
        client.loop_stop()

def simple_on_message(client, userdata, msg):
    """
    一个极简的 on_message 回调函数。
    它的唯一作用是打印收到的消息主题和内容。

    参数解释:
        - client: 触发此回调的客户端实例。
        - userdata: 在创建客户端时传入的任何用户自定义数据 (在这个简单示例中未使用)。
        - msg: 一个包含消息所有信息的对象。
            - msg.topic (str): 消息发布到的主题。
            - msg.payload (bytes): 消息的载荷/内容，为字节类型。
            - msg.qos (int): 消息的服务质量等级。
            - msg.retain (bool): 是否为保留消息。
    """
    """
        这个 on_message 函数只负责“路由分发”，不处理具体业务。
        """
    print(f"\n📩 [路由器] 收到消息，主题: {msg.topic}，准备路由...")

    # 使用 paho-mqtt 自带的 topic_matches_sub 工具来安全地匹配主题，支持通配符
    if mqtt.topic_matches_sub("+/response", msg.topic):
        handle_device_command(client, msg)


def on_connect_handle_lan_1(accesscode, ip, client, userdata, flags, rc):
    """
    连接成功后，执行核心的订阅和发布测试。
    """
    if rc == 0:
        print(f"✅ [设备 {'clientId'}] 连接成功!")
        # 1. 订阅所有指定主题
        print("\n🚀 开始订阅主题...")
        topic1=f"{accesscode}/config/request"
        topic = f"{accesscode}/config/response"
        client.subscribe(topic, qos=1)
        print(f"  -> 已订阅: {topic}")
        # 2. 向所有指定主题发布一条测试消息
        print("\n🚀 开始发布消息...")
        test_message = {
        "jsonrpc": "2.0",
        "method": "server.request_key",
        "params": {
            "clientid": f"{ip}",
        },
        "id": 123
        }
        test_message = json.dumps(test_message)
        client.publish(topic1, test_message, qos=1)
        print(f"  -> 已向主题 '{topic}' 发布消息: '{test_message}'")

    else:
        print(f"❌ [设备 {'clientId'}] 连接失败，返回码: {rc}")
        client.loop_stop()

def on_message_handle_lan_1(shared_state, client, userdata, msg):
    """
    改造后的 on_message，第一个参数是外部传入的共享状态字典。
    注意：这里的 'userdata' 参数是由 paho-mqtt 传入的，但我们没有使用它。
    """
    print(f"\n📩 [回调] 收到消息! 主题: {msg.topic} (通过 partial)")

    if not isinstance(shared_state, dict):
        print("❌ [回调] 错误: 传入的共享状态不是一个字典！")
        client.loop_stop()
        return

    try:
        certs_data = json.loads(msg.payload)

        # --- 关键改动 ---
        # 和之前一样，直接修改传入的共享状态字典
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".pem") as ca_file, \
                tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".pem") as cert_file, \
                tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".key") as key_file:

            ca_file.write(certs_data['result']['ca'])
            cert_file.write(certs_data['result']['cert'])
            key_file.write(certs_data['result']['key'])

            shared_state['temp_files'] = {
                'ca': ca_file.name,
                'cert': cert_file.name,
                'key': key_file.name,
            }
            shared_state['client_id'] = certs_data['result']['clientid']
            shared_state['sn'] = certs_data['result']['sn']
            shared_state['certificates_received'] = True

        print("✅ [回调] 证书解析成功，状态已更新。")
        client.disconnect()
        client.loop_stop()

    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ [回调] 解析证书消息失败: {e}")
        shared_state['certificates_received'] = False
        client.loop_stop()

# --- 主逻辑 ---

def load_and_prepare_credentials(credentials_data: dict):
    """
    加载从参数传入的字典格式的凭证数据，并准备证书文件。

    Args:
        credentials_data (dict): 包含完整凭证信息的Python字典。
                                 这通常是 `json.load()` 或 API 响应的结果。
    """
    global CONFIG, PUBLISH_TOPICS, SUBSCRIBE_TOPICS

    print("ℹ️ 正在从传入的参数中加载和准备凭证...")

    # 1. 直接使用传入的字典，不再从文件读取
    # 检查返回码是否为成功
    if credentials_data.get("code") != 200:
        raise ValueError("凭证数据中的返回码不是200，无法继续。")

    CONFIG = credentials_data['data']

    # 2. 将JSON中的证书和私钥字符串写入临时文件
    # paho-mqtt库需要文件路径，而不是字符串
    temp_cert_dir = "temp_certs"
    if not os.path.exists(temp_cert_dir):
        os.makedirs(temp_cert_dir)

    client_cert_path = os.path.join(temp_cert_dir, "client.crt")
    client_key_path = os.path.join(temp_cert_dir, "client.key")

    with open(client_cert_path, "w") as f:
        f.write(CONFIG['secretId'])
    with open(client_key_path, "w") as f:
        f.write(CONFIG['secretKey'])

    # 将临时文件路径存回配置，方便后续使用
    CONFIG['client_cert_path'] = client_cert_path
    CONFIG['client_key_path'] = client_key_path

    # 3. 处理主题列表，加上前缀
    prefix = CONFIG.get("pathPrefix", "")
    PUBLISH_TOPICS = [prefix + t for t in CONFIG["topics"]["publish"]]
    SUBSCRIBE_TOPICS = [prefix + t for t in CONFIG["topics"]["subscribe"]]

    print("✅ 凭证准备完毕!")
    return CONFIG
def connect(config):
    try:
        client = mqtt.Client(client_id=CONFIG['clientId'])
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        client.tls_set(ca_certs="AmazonRootCA1.pem",
                       certfile=CONFIG['client_cert_path'],
                       keyfile=CONFIG['client_key_path'],
                       cert_reqs=ssl.CERT_REQUIRED,
                       tls_version=ssl.PROTOCOL_TLS)

        print("🚀 正在尝试连接...")
        client.connect(CONFIG['endpoint'], CONFIG['port'])

        # loop_forever() 会一直运行，直到在回调函数中调用 disconnect() 和 loop_stop()
        client.loop_forever()

    except Exception as e:
        print(f"💥 程序运行时发生错误: {e}")

def handle_device_command(client, msg):
    print(json.loads(msg.payload))