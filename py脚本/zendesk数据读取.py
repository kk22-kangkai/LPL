import json
import requests
from requests.auth import HTTPBasicAuth

# ----- 请修改以下配置 -----
local_json_file_path = 'C:/Users/Snapmaker/Downloads/zendesk_tickets_2025_5_11_part1.json'  # 替换为你的本地 JSON 文件路径
zendesk_domain = 'snapmaker.zendesk.com'  # 从你的 JSON 数据中提取的域名
email_address = ' jasmine.xie@snapmaker.com'  # 替换为你的 Zendesk 邮箱地址
api_token = '1vQwYoPB0GhURF2o49wl4xB4KP3LMs8QEoOISkyM'  # 替换为你的 Zendesk API token
output_json_file_path = 'output.json'  # 设置输出 JSON 文件路径
# --------------------------

def extract_and_request():
    """
    从本地 JSON 文件中提取 id，并请求 Zendesk API 获取数据，并将结果保存到 JSON 文件。
    """
    try:
        with open(local_json_file_path, 'r', encoding='utf-8') as f:
            local_data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到本地 JSON 文件 {local_json_file_path}")
        return

    results = []
    auth = HTTPBasicAuth(f'{email_address}/token', api_token)
    headers = {"Content-Type": "application/json"}

    for item in local_data:
        ticket_id_local = item.get('id')
        local_status = item.get('status')
        local_score = item.get('satisfaction_rating', {}).get('score')
        local_is_public = item.get('is_public')

        if ticket_id_local:
            api_url = f"https://{zendesk_domain}/api/v2/tickets/{ticket_id_local}/metrics"
            try:
                response = requests.get(api_url, auth=auth, headers=headers,verify=False)
                response.raise_for_status()  # 如果状态码不是 200，则抛出异常
                api_data = response.json().get('ticket_metric')
                # print(api_data)
                if api_data and len(api_data) > 0:
                    metric = api_data
                    ticket_id = metric.get('ticket_id')
                    created_at = metric.get('created_at')
                    solved_at = metric.get('solved_at')
                    status_updated_at = metric.get('status_updated_at')
                    latest_comment_added_at = metric.get('latest_comment_added_at')
                    reopens = metric.get('reopens')
                    replies = metric.get('replies')
                    first_resolution_calendar = metric.get('first_resolution_time_in_minutes', {}).get('calendar')
                    full_resolution_calendar = metric.get('full_resolution_time_in_minutes', {}).get('calendar')
                    requester_wait_calendar = metric.get('requester_wait_time_in_minutes', {}).get('calendar')

                    results.append({
                        "ticket_id": ticket_id,
                        "created_at": created_at,
                        "solved_at": solved_at,
                        "status_updated_at": status_updated_at,
                        "latest_comment_added_at": latest_comment_added_at,
                        "reopens": reopens,
                        "replies": replies,
                        "first_resolution_time_in_minutes": first_resolution_calendar,
                        "full_resolution_time_in_minutes": full_resolution_calendar,
                        "requester_wait_time_in_minutes": requester_wait_calendar,
                        "local_status": local_status,
                        "local_score": local_score,
                        "local_is_public": local_is_public
                    })
                else:
                    print(f"警告：从 API 未获取到工单指标数据，ticket_id={ticket_id_local}")
            except requests.exceptions.RequestException as e:
                print(f"请求 API 时发生错误 (ticket_id={ticket_id_local}): {e}")
            except json.JSONDecodeError:
                print(f"解析 API 响应 JSON 失败 (ticket_id={ticket_id_local}): {response.text}")
        else:
            print("警告：本地 JSON 数据中找不到 'id' 字段")

    # 将结果保存到 JSON 文件
    try:
        with open(output_json_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(results, outfile, ensure_ascii=False, indent=2)
        print(f"结果已保存到文件: {output_json_file_path}")
    except Exception as e:
        print(f"保存结果到文件时发生错误: {e}")

if __name__ == "__main__":
    extract_and_request()