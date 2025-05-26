import os


def merge_md_files(root_dir_param, output_file_param):
    """
    递归地查找 root_dir_param 中的所有 .md 文件，
    并将它们合并到 output_file_param 指定的单个文件中，
    每个原始文件的内容之间用 '===' (实际为换行符 + === + 换行符) 分隔。

    Args:
        root_dir_param (str): 要搜索 .md 文件的目录路径。
        output_file_param (str): 输出的合并后 .md 文件的路径。
    """
    md_contents = []
    file_paths_to_process = []

    # 解析为绝对路径以增强稳健性
    abs_root_dir = os.path.abspath(root_dir_param)
    abs_output_file_path = os.path.abspath(output_file_param)

    if not os.path.isdir(abs_root_dir):
        print(f"错误：输入目录 '{abs_root_dir}' (来自配置 '{root_dir_param}') 未找到或不是一个有效的目录。")
        return

    print(f"开始在目录 '{abs_root_dir}' 中查找 .md 文件...")

    # 1. 收集所有 .md 文件的路径，同时排除输出文件本身
    for dirpath, _, filenames in os.walk(abs_root_dir):
        for filename in filenames:
            # 不区分大小写地检查 .md 后缀
            if filename.lower().endswith(".md"):
                current_file_path = os.path.abspath(os.path.join(dirpath, filename))
                # 如果当前文件不是目标输出文件，则添加到待处理列表
                if current_file_path != abs_output_file_path:
                    file_paths_to_process.append(current_file_path)
                else:
                    print(f"提示：跳过输出文件本身 '{current_file_path}'，不将其作为输入。")

    # 2. 对文件路径进行排序，以确保合并顺序的一致性
    file_paths_to_process.sort()

    if not file_paths_to_process:
        print(f"在 '{abs_root_dir}' 中没有找到需要合并的 .md 文件 (已排除可能的输出文件)。")
        # 如果没有找到文件，可以选择创建一个空的输出文件
        try:
            output_dir_for_empty_file = os.path.dirname(abs_output_file_path)
            if output_dir_for_empty_file and not os.path.exists(output_dir_for_empty_file):
                os.makedirs(output_dir_for_empty_file)
                print(f"已创建输出目录：'{output_dir_for_empty_file}'")
            with open(abs_output_file_path, 'w', encoding='utf-8') as outfile:
                outfile.write("")  # 创建一个空文件
            print(f"已在 '{abs_output_file_path}' 创建空的输出文件。")
        except Exception as e:
            print(f"创建空的输出文件 '{abs_output_file_path}' 时发生错误: {e}")
        return

    print(f"找到 {len(file_paths_to_process)} 个 .md 文件准备合并。")

    # 3. 读取每个文件的内容
    for i, filepath in enumerate(file_paths_to_process):
        try:
            with open(filepath, 'r', encoding='utf-8') as infile:
                print(f"正在读取 ({i + 1}/{len(file_paths_to_process)}): {filepath}")
                md_contents.append(infile.read())
        except Exception as e:
            print(f"读取文件 {filepath} 时发生错误: {e}")
            # 可选: 在合并内容中为读取失败的文件添加错误标记
            # md_contents.append(f"\n\n--- 文件读取错误: {filepath} ---\n错误详情: {e}\n\n")

    # 4. 定义分隔符并合并内容
    # 我们在 '===' 上下各加一个换行符，使原始的合并文档更易读。
    # 如果您严格需要不带任何换行符的 "===" 作为分隔符，请修改为: separator = "==="
    separator = "\n===SEPARATOR===\n"
    merged_content = separator.join(md_contents)

    # 5. 写入到输出文件
    try:
        # 确保输出文件所在的目录存在
        output_dir = os.path.dirname(abs_output_file_path)
        # 如果 output_dir 不为空 (例如，不是当前目录下的文件名) 且目录不存在，则创建
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"已创建输出目录：'{output_dir}'")

        with open(abs_output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(merged_content)
        print(f"\n成功合并所有 .md 文件到 '{abs_output_file_path}'。")

        if len(md_contents) > 1:
            print(f"每个原始文档的内容之间已用 '{separator.strip()}' 作为分隔符。")
        elif len(md_contents) == 1:
            print("只找到一个 .md 文件，输出文件内容与原始文件相同，未使用分隔符。")

    except Exception as e:
        print(f"写入输出文件 '{abs_output_file_path}' 时发生错误: {e}")


if __name__ == '__main__':
    # --- 用户配置区域 ---
    # 请将 'your_markdown_files_directory' 替换为包含您的 .md 文件的实际目录路径
    # 例如在 Windows 上: r"C:\Users\YourUser\Documents\MyNotes"
    # 例如在 macOS/Linux 上: "/home/youruser/documents/markdown_docs"
    # 或者使用相对路径，例如 "data/md_files" (此相对路径是相对于脚本运行的位置)
    input_directory = "D:\PythonProject\pre_sales_articles"

    # 请将 'merged_document.md' 替换为您希望生成的合并后 .md 文件的名称或完整路径
    # 例如: "all_notes_merged.md"
    # 或指定包含路径的名称: "output/final_merged_document.md"
    output_merged_file = "E:\WIKI\SupportM.md"
    # --- 配置结束 ---

    # 如果用户未修改默认的 input_directory，给一个提示
    default_input_dir_check = "your_markdown_files_directory"
    if input_directory == default_input_dir_check:
        print(f"提示：脚本当前配置的输入目录是 '{default_input_dir_check}'。")
        print(f"如果您尚未修改脚本，这可能不是您期望的目录。")
        try:
            user_input_dir = input(
                f"请输入您的 Markdown 文件所在目录的路径，或按 Enter 使用默认值 (并祈祷它存在): ").strip()
            if user_input_dir:
                input_directory = user_input_dir
        except KeyboardInterrupt:
            print("\n操作已取消。")
            exit()

        if not os.path.isdir(os.path.abspath(input_directory)):
            print(f"错误：最终确定的输入目录 '{os.path.abspath(input_directory)}' 无效或不存在。请检查路径。")
            print("脚本将退出。请修改脚本中的 'input_directory' 变量或在提示时提供有效路径。")
            exit()

    merge_md_files(input_directory, output_merged_file)