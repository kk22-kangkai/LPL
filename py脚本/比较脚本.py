import pandas as pd
import os
import sys

def merge_xlsx_to_single_sheet(input_files, output_file, output_sheet_name="汇总数据"):
    """
    将多个 XLSX 文件的第一个工作表数据合并（追加）到输出文件中的单个工作表。

    参数:
        input_files (list): 输入 XLSX 文件路径的列表。
        output_file (str): 输出 XLSX 文件的路径。
        output_sheet_name (str): 输出文件中合并数据的工作表名称。
    """
    # 检查所有输入文件是否存在
    for file_path in input_files:
        if not os.path.isfile(file_path):
            print(f"错误：输入文件 '{file_path}' 未找到。")
            return
        if not file_path.lower().endswith('.xlsx'):
            print(f"错误：文件 '{file_path}' 不是一个 .xlsx 文件。")
            return

    if not output_file.lower().endswith('.xlsx'):
        output_file_adjusted = output_file + '.xlsx'
        print(f"输出文件名已自动添加 .xlsx 后缀: '{output_file_adjusted}' (原为 '{output_file}')")
        output_file = output_file_adjusted


    all_data = []
    try:
        print("\n开始读取输入文件:")
        for file_path in input_files:
            try:
                # 读取当前 Excel 文件的第一个工作表 (sheet_name=0)
                df = pd.read_excel(file_path, sheet_name=0)
                all_data.append(df)
                print(f"  成功读取文件 '{file_path}' 的第一个工作表。")
            except Exception as e:
                print(f"  读取文件 '{file_path}' 时出错: {e}")
                # 你可以选择如果一个文件读取失败是否继续
                # return # 如果希望在遇到错误时停止，取消此行注释

        if not all_data:
            print("没有数据可合并。请检查输入文件是否为空或读取是否成功。")
            return

        # 合并所有 DataFrame
        # ignore_index=True 会重新生成合并后 DataFrame 的索引
        print("\n正在合并数据...")
        merged_df = pd.concat(all_data, ignore_index=True)
        print("数据合并完成。")

        # 将合并后的 DataFrame 写入新的 Excel 文件
        print(f"正在将合并数据写入到 '{output_file}' 的 '{output_sheet_name}' 工作表中...")
        merged_df.to_excel(output_file, sheet_name=output_sheet_name, index=False, engine='openpyxl')
        print(f"所有指定的 XLSX 文件已成功合并到 '{output_file}' 的 '{output_sheet_name}' 工作表中。")

    except Exception as e:
        print(f"在合并数据或写入输出文件 '{output_file}' 时发生严重错误: {e}")

def merge_xlsx_to_multiple_sheets(input_files, output_file):
    """
    将多个 XLSX 文件的第一个工作表合并到单个 XLSX 文件中，
    每个输入文件的第一个工作表成为输出文件中的一个新工作表。

    参数:
        input_files (list): 输入 XLSX 文件路径的列表。
        output_file (str): 输出合并后 XLSX 文件的路径。
    """
    # 检查所有输入文件是否存在
    for file_path in input_files:
        if not os.path.isfile(file_path):
            print(f"错误：输入文件 '{file_path}' 未找到。")
            return
        if not file_path.lower().endswith('.xlsx'):
            print(f"错误：文件 '{file_path}' 不是一个 .xlsx 文件。")
            return

    if not output_file.lower().endswith('.xlsx'):
        output_file_adjusted = output_file + '.xlsx'
        print(f"输出文件名已自动添加 .xlsx 后缀: '{output_file_adjusted}' (原为 '{output_file}')")
        output_file = output_file_adjusted

    try:
        print(f"\n准备将不同文件合并到 '{output_file}' 的不同工作表中...")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for i, file_path in enumerate(input_files):
                try:
                    # 读取当前 Excel 文件的第一个工作表 (sheet_name=0)
                    df = pd.read_excel(file_path, sheet_name=0)

                    # 使用文件名（不含扩展名）作为工作表名
                    # 如果需要，可以添加更复杂的逻辑来处理潜在的重名或过长的工作表名
                    base_name = os.path.basename(file_path)
                    sheet_name = os.path.splitext(base_name)[0]
                    # 确保工作表名唯一且长度合适 (Excel 工作表名长度限制约为31个字符)
                    sheet_name = f"{sheet_name[:25]}_{i+1}" #截断并添加序号以确保唯一性

                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  文件 '{file_path}' 的第一个工作表已添加到输出文件的 '{sheet_name}' 工作表中。")
                except Exception as e:
                    print(f"  处理文件 '{file_path}' 时出错: {e}")
        print(f"所有指定的 XLSX 文件已成功合并到 '{output_file}' 的不同工作表中。")
    except Exception as e:
        print(f"创建或写入输出文件 '{output_file}' 时发生严重错误: {e}")

if __name__ == "__main__":
    # --- 配置区 ---
    # 请将下面的文件名替换为你的实际文件名
    # 确保这些文件与脚本在同一目录下，或者提供完整路径
    input_excel_files = [
        "output_makerworld_data_csv_input.xlsx",
        "output_makerworld_data_csv_input2.xlsx",
        "output_makerworld_data_csv_input3.xlsx",
        "output_makerworld_data_csv_input4.xlsx"
    ]

    # 定义输出文件名
    output_excel_single_sheet = "合并后_单工作表.xlsx"
    output_excel_multiple_sheets = "合并后_多工作表.xlsx"

    # --- 选择合并方式 ---
    # 你可以选择以下两种方式之一来合并你的 Excel 文件。
    # 取消注释你想要使用的方式，并注释掉另一个。

    # **方式一：将所有 XLSX 文件的数据追加合并到输出文件中的单个工作表**
    # 这是最常见的数据汇总方式。
    print("执行方式一：合并到单个工作表")
    merge_xlsx_to_single_sheet(input_excel_files, output_excel_single_sheet, output_sheet_name="合并后的所有数据")

    # **方式二：将每个 XLSX 文件合并为输出文件中的不同工作表**
    # 如果你想使用这种方式，请注释掉上面的 `merge_xlsx_to_single_sheet` 调用，并取消下面这行的注释：
    # print("\n执行方式二：合并到多个工作表")
    # merge_xlsx_to_multiple_sheets(input_excel_files, output_excel_multiple_sheets)


    # --- 安装提示 ---
    print("\n---")
    print("脚本执行完毕。")
    print("请确保你已经安装了必要的 Python 库: pandas 和 openpyxl。")
    print("如果尚未安装，你可以在命令行中使用以下命令进行安装:")
    print("pip install pandas openpyxl")