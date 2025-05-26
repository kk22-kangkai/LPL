import pandas as pd

# --- 配置参数 ---
input_file = "合并后_单工作表.xlsx"
sheet_to_process = 0  # 0 代表第一个工作表
label_column_name = "标签"
delimiter = ","  # 分隔符是逗号
output_column_secondary = "二级标签"  # 拆分后的第一部分
output_column_primary = "一级标签"    # 拆分后的第二部分
output_file_name_base = "模型数据"    # 输出文件的基本名
output_file = f"{output_file_name_base}.xlsx" # 完整的输出文件名

print(f"--- 开始处理脚本 ---")
print(f"输入文件: {input_file}")
print(f"待处理列: '{label_column_name}'")
print(f"分隔符: '{delimiter}'")
print(f"输出列 (二级): '{output_column_secondary}'")
print(f"输出列 (一级): '{output_column_primary}'")
print(f"输出文件: {output_file}")
print("--------------------")

try:
    # 1. 读取Excel文件
    print(f"\n[1/5] 正在读取文件 '{input_file}'...")
    try:
        df = pd.read_excel(input_file, sheet_name=sheet_to_process)
        print("     文件读取成功。")
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_file}' 未找到。请确保文件名和路径正确无误，并且该文件与脚本在同一目录下，或使用了完整路径。")
        exit() # 如果文件未找到，则退出脚本
    except Exception as e:
        print(f"错误：读取文件 '{input_file}' 时发生错误: {e}")
        exit()

    # 2. 检查“标签”列是否存在
    print(f"\n[2/5] 正在检查列 '{label_column_name}' 是否存在...")
    if label_column_name not in df.columns:
        print(f"错误：在文件 '{input_file}' (工作表: {sheet_to_process if isinstance(sheet_to_process, str) else '第一个'}) 中未找到名为 '{label_column_name}' 的列。")
        print(f"文件中可用的列为: {df.columns.tolist()}")
        exit() # 如果列未找到，则退出脚本
    print(f"     列 '{label_column_name}' 已找到。")

    # 3. 拆分“标签”列
    #    使用 .astype(str) 确保列中的数据为字符串类型，避免非字符串类型数据导致 split 方法出错
    #    n=1 表示只按第一个分隔符拆分，得到最多两个部分
    #    expand=True 会将拆分结果直接放入新的DataFrame列中
    print(f"\n[3/5] 正在拆分 '{label_column_name}' 列 (按第一个 '{delimiter}' 分隔)...")
    split_data = df[label_column_name].astype(str).str.split(delimiter, n=1, expand=True)
    print("     列数据拆分操作完成。")

    # 4. 创建新列并赋值
    #    第一部分 -> 二级标签
    #    第二部分 -> 一级标签
    print(f"\n[4/5] 正在创建新列 '{output_column_secondary}' 和 '{output_column_primary}'...")
    # 为“二级标签”列赋值，并去除可能存在的前后空格
    df[output_column_secondary] = split_data[0].str.strip()

    # 检查拆分后是否存在第二部分 (即原始数据中是否有逗号，并且逗号不在字符串末尾)
    if split_data.shape[1] > 1:
        # 为“一级标签”列赋值，并去除可能存在的前后空格
        df[output_column_primary] = split_data[1].str.strip()
    else:
        # 如果没有第二部分（例如，原始标签中没有逗号，或逗号在末尾），则将“一级标签”设为空值
        df[output_column_primary] = pd.NA # 或者使用 "" 代表空字符串: df[output_column_primary] = ""
        print(f"     提示：某些行的 '{label_column_name}' 列可能没有找到分隔符 '{delimiter}' 或分隔符在末尾，对应的 '{output_column_primary}' 将被设置为空值。")
    print(f"     新列 '{output_column_secondary}' 和 '{output_column_primary}' 已创建并赋值。")


    # 5. 保存到新的Excel文件
    print(f"\n[5/5] 正在将结果保存到 '{output_file}'...")
    try:
        df.to_excel(output_file, index=False, engine='openpyxl') # index=False 表示不将DataFrame的索引写入Excel文件
        print(f"     处理完成！已成功将结果保存到 '{output_file}'。")
    except Exception as e:
        print(f"错误：保存文件 '{output_file}' 时发生错误: {e}")

    print("\n--- 脚本执行结束 ---")

except Exception as e:
    # 捕获上面未明确捕获的其他任何潜在错误
    print(f"处理过程中发生未预料的严重错误：{e}")