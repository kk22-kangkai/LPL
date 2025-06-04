import json


def process_ticket_metrics_from_file(filepath):
    """
    从指定的JSON文件读取工单指标数据，并逐个处理每个工单的指标。

    参数:
    filepath (str): JSON文件的路径。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 从文件加载JSON数据
    except FileNotFoundError:
        print(f"错误：文件 '{filepath}' 未找到。")
        return
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: 文件 '{filepath}' 中的内容不是有效的JSON格式。错误信息: {e}")
        return
    except Exception as e:
        print(f"读取或解析文件 '{filepath}' 时发生未知错误：{e}")
        return

    # 检查 "ticket_metrics" 键是否存在并且其值是一个列表
    if "ticket_metrics" in data and isinstance(data["ticket_metrics"], list):
        ticket_metrics_list = data["ticket_metrics"]
        print(f"成功从文件 '{filepath}' 解析JSON，找到 {len(ticket_metrics_list)} 条工单指标记录。开始处理：")

        for index, metric in enumerate(ticket_metrics_list):
            print(f"\n--- 正在处理第 {index + 1} 条工单指标 (Ticket ID: {metric.get('ticket_id', 'N/A')}) ---")

            # 访问并打印一些关键字段 (使用 .get() 更安全，以防字段不存在)
            print(f"  指标ID (Metric ID): {metric.get('id', 'N/A')}")
            print(f"  工单创建时间 (Created At): {metric.get('created_at', 'N/A')}")
            print(f"  工单解决时间 (Solved At): {metric.get('solved_at', 'N/A')}")
            print(f"  工单状态更新时间 (Status Updated At): {metric.get('status_updated_at', 'N/A')}")
            print(f"  最新评论添加时间 (Latest Comment Added At): {metric.get('latest_comment_added_at', 'N/A')}")
            print(f"  重开次数 (Reopens): {metric.get('reopens', 'N/A')}")
            print(f"  回复次数 (Replies): {metric.get('replies', 'N/A')}")

            # 处理嵌套对象，例如 *_time_in_minutes
            first_resolution_time = metric.get("first_resolution_time_in_minutes", {})
            print(f"  首次解决时间 (分钟) - 日历时: {first_resolution_time.get('calendar', 'N/A')}")
            print(f"  首次解决时间 (分钟) - 工作时: {first_resolution_time.get('business', 'N/A')}")

            full_resolution_time = metric.get("full_resolution_time_in_minutes", {})
            print(f"  完全解决时间 (分钟) - 日历时: {full_resolution_time.get('calendar', 'N/A')}")
            print(f"  完全解决时间 (分钟) - 工作时: {full_resolution_time.get('business', 'N/A')}")

            requester_wait_time = metric.get("requester_wait_time_in_minutes", {})
            print(f"  请求者等待时间 (分钟) - 日历时: {requester_wait_time.get('calendar', 'N/A')}")
            # print(f"  请求者等待时间 (分钟) - 工作时: {requester_wait_time.get('business', 'N/A')}")

            # 在这里添加你自己的具体处理逻辑
            if metric.get('reopens', 0) == 0 and metric.get('replies', -1) <= 1:
                print(f"  工单 {metric.get('ticket_id')} 可能是一次性解决。")

            print("  --------------------------------------------------")

        print("\n所有工单指标记录处理完毕。")

    else:
        print(f"错误：文件 '{filepath}' 的JSON数据中未找到 'ticket_metrics' 键，或者其值不是一个列表。")


# --- 调用函数处理JSON数据 ---
if __name__ == "__main__":
    # 定义你的JSON文件路径
    json_file_path = "C:/Users/Snapmaker/Downloads/Code2.json"  # 请将此替换为你的实际文件名
    process_ticket_metrics_from_file(json_file_path)