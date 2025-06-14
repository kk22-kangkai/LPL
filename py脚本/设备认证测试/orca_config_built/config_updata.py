import json
import argparse
from pathlib import Path
from typing import Dict, Any

# --- 配置 (保持不变) ---
EXCLUSION_KEYS = frozenset([
    "from", "inherits", "is_custom_defined", "name",
    "print_settings_id", "version"
])

# --- 全局缓存 (保持不变) ---
file_path_cache: Dict[str, Path] = {}


def find_all_json_files(search_dir: Path) -> None:
    """
    (此函数保持不变)
    递归扫描目录，构建文件名（不含扩展名）到完整路径的映射。
    """
    print(f"INFO: 正在扫描 '{search_dir}' 以建立全局文件索引...")
    if not file_path_cache:  # 只有在缓存为空时才扫描
        for path_object in search_dir.rglob('*.json'):
            filename_no_ext = path_object.stem
            file_path_cache[filename_no_ext] = path_object
        print(f"INFO: 索引完成，找到 {len(file_path_cache)} 个JSON文件。")
    else:
        print("INFO: 全局文件索引已存在，跳过扫描。")


def update_parent_file(child_file: Path) -> None:
    """
    (此函数保持不变)
    用子文件的配置来更新其直接父文件。
    """
    print(f"\n--- 处理文件: {child_file.name} ---")

    try:
        with open(child_file, 'r', encoding='utf-8') as f:
            child_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: 读取或解析子文件 '{child_file}' 失败: {e}")
        return

    parent_name = child_data.get("inherits")
    if not parent_name:
        print(f"INFO: 文件没有 'inherits' 字段，跳过。")
        return

    print(f"INFO: 指向父级 '{parent_name}'。")

    parent_path = file_path_cache.get(parent_name)
    if not parent_path:
        print(f"ERROR: 在索引中找不到父文件 '{parent_name}.json'。")
        return

    try:
        with open(parent_path, 'r', encoding='utf-8') as f:
            parent_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: 读取或解析父文件 '{parent_path}' 失败: {e}")
        return

    original_parent_data_str = json.dumps(parent_data, sort_keys=True)

    for key, value in child_data.items():
        if key not in EXCLUSION_KEYS:
            parent_data[key] = value

    new_parent_data_str = json.dumps(parent_data, sort_keys=True)
    if new_parent_data_str == original_parent_data_str:
        print("INFO: 无需更新，父文件已是最新状态。")
        return

    print(f"INFO: 检测到变更，正在更新父文件 '{parent_path.name}'...")
    try:
        with open(parent_path, 'w', encoding='utf-8') as f:
            json.dump(parent_data, f, indent=4, ensure_ascii=False)
        print(f"SUCCESS: 已成功更新 '{parent_path.name}'。")
    except IOError as e:
        print(f"ERROR: 写入父文件 '{parent_path}' 失败: {e}")


def main():
    # --- 命令行接口已更新 ---
    parser = argparse.ArgumentParser(
        description="批量处理一个目录下的所有JSON文件，用它们的配置去更新各自指向的父文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target_directory",  # 参数变为目标目录
        type=str,
        help="要批量处理的、包含所有子JSON文件的目标目录。"
    )
    parser.add_argument(
        "search_directory",
        type=str,
        help="包含所有JSON文件（包括父文件）的全局搜索根目录。"
    )
    args = parser.parse_args()

    target_dir_path = Path(args.target_directory)
    search_dir_path = Path(args.search_directory)

    if not target_dir_path.is_dir():
        print(f"ERROR: 目标目录不存在: {target_dir_path}")
        return
    if not search_dir_path.is_dir():
        print(f"ERROR: 搜索目录不存在: {search_dir_path}")
        return

    # 1. 预处理：扫描并缓存所有JSON文件的位置
    find_all_json_files(search_dir_path)

    # 2. 核心处理：遍历目标目录下的所有JSON文件并逐一处理
    print(f"\n{'=' * 40}\n开始批量处理目标目录 '{target_dir_path}'\n{'=' * 40}")

    processed_count = 0
    # 递归查找目标目录下的所有 .json 文件
    target_files = list(target_dir_path.rglob('*.json'))

    if not target_files:
        print("INFO: 在目标目录中未找到任何JSON文件。")
        return

    for child_file_path in target_files:
        update_parent_file(child_file_path)
        processed_count += 1

    print(f"\n{'=' * 40}\n批量处理完成。共处理了 {processed_count} 个文件。\n{'=' * 40}")


if __name__ == "__main__":
    main()