import json

def extract_and_write_ticket_metrics_to_file(input_filepath, output_filepath):
    """
    从指定的输入JSON文件读取工单指标数据，提取关键信息，
    并将这些提取出的信息写入一个新的JSON文件。

    参数:
    input_filepath (str): 包含原始工单指标数据的JSON文件的路径。
    output_filepath (str): 将提取出的数据写入的新JSON文件的路径。
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 从文件加载JSON数据
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_filepath}' 未找到。")
        return
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: 文件 '{input_filepath}' 中的内容不是有效的JSON格式。错误信息: {e}")
        return
    except Exception as e:
        print(f"读取或解析文件 '{input_filepath}' 时发生未知错误：{e}")
        return

    extracted_metrics = []

    # 检查 "ticket_metrics" 键是否存在并且其值是一个列表
    if "ticket_metrics" in data and isinstance(data["ticket_metrics"], list):
        ticket_metrics_list = data["ticket_metrics"]
        print(f"成功从文件 '{input_filepath}' 解析JSON，找到 {len(ticket_metrics_list)} 条工单指标记录。开始提取并转换：")

        for index, metric in enumerate(ticket_metrics_list):
            # 提取你想要写入新JSON文件的关键字段
            ticket_id = metric.get('ticket_id', 'N/A')
            created_at = metric.get('created_at', 'N/A')
            solved_at = metric.get('solved_at', 'N/A')
            status_updated_at = metric.get('status_updated_at', 'N/A')
            latest_comment_added_at = metric.get('latest_comment_added_at', 'N/A')
            reopens = metric.get('reopens', 0)
            replies = metric.get('replies', 0)

            first_resolution_calendar = metric.get("first_resolution_time_in_minutes", {}).get('calendar', 'N/A')
            first_resolution_business = metric.get("first_resolution_time_in_minutes", {}).get('business', 'N/A')

            full_resolution_calendar = metric.get("full_resolution_time_in_minutes", {}).get('calendar', 'N/A')
            full_resolution_business = metric.get("full_resolution_time_in_minutes", {}).get('business', 'N/A')

            requester_wait_calendar = metric.get("requester_wait_time_in_minutes", {}).get('calendar', 'N/A')
            requester_wait_business = metric.get("requester_wait_time_in_minutes", {}).get('business', 'N/A')

            # 创建一个字典来存储提取出的信息
            extracted_info = {
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
                "is_one_time_resolution": (reopens == 0 and replies <= 1) # 添加一个判断字段
            }
            extracted_metrics.append(extracted_info)
            print(f"  已提取第 {index + 1} 条记录 (Ticket ID: {ticket_id})")

        # 将提取出的数据写入新的JSON文件
        try:
            with open(output_filepath, 'w', encoding='utf-8') as outfile:
                json.dump(extracted_metrics, outfile, indent=4, ensure_ascii=False)
            print(f"\n成功将 {len(extracted_metrics)} 条工单指标数据写入到文件 '{output_filepath}'。")
        except IOError as e:
            print(f"写入输出文件 '{output_filepath}' 时发生错误: {e}")
        except Exception as e:
            print(f"写入输出文件 '{output_filepath}' 时发生未知错误: {e}")

    else:
        print(f"错误：文件 '{input_filepath}' 的JSON数据中未找到 'ticket_metrics' 键，或者其值不是一个列表。")

if __name__ == "__main__":
    # 定义你的输入和输出JSON文件路径
    input_json_file_path = "C:/Users/Snapmaker/Downloads/Code2.json"  # 请将此替换为你的实际输入文件名
    output_json_file_path = "C:/Users/Snapmaker/Downloads/extracted_ticket.json" # 你希望生成的新文件名

    # 调用函数来处理并写入数据
    extract_and_write_ticket_metrics_to_file(input_json_file_path, output_json_file_path)