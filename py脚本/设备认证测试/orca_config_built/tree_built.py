import json
from pathlib import Path
from typing import Dict, Union, Optional, Any


def create_inheritance_map_v2(root_directory: Union[str, Path]) -> Dict[str, Optional[Any]]:
    """
    递归遍历一个目录，从所有 JSON 文件中提取 "inherits" 字段。
    如果字段不存在，则其值被设置为 None。
    最终创建一个以文件名（不含扩展名）为键的映射表。

    :param root_directory: 要扫描的根目录路径（可以是字符串或 Path 对象）。
    :return: 一个包含 {文件名: inherits值 或 None} 的字典。
    """
    root_path = Path(root_directory)
    inheritance_map = {}

    if not root_path.is_dir():
        print(f"错误: 路径 '{root_directory}' 不是一个有效的目录。")
        return inheritance_map

    print(f"正在扫描 '{root_path}' 及其子目录...")
    for json_path in root_path.rglob('*.json'):
        key = json_path.stem

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 使用 .get() 方法安全地获取值。
                # 如果 'inherits' 键存在，则获取其值；否则，返回 None。
                value = data.get('inherits', None)

                # 无论如何都将条目添加到映射表中
                inheritance_map[key] = value

                # 更新打印信息以反映新逻辑
                if value is not None:
                    print(f"  - 找到: '{json_path.name}' -> 继承自 '{value}'")
                else:
                    print(f"  - 处理: '{json_path.name}' -> 无继承 (设置为 None)")

        except json.JSONDecodeError:
            print(f"  - 错误: 无法解析 '{json_path.name}'，文件可能不是有效的JSON。")
        except Exception as e:
            print(f"  - 错误: 处理 '{json_path.name}' 时发生未知错误: {e}")

    return inheritance_map


# --- 如何使用 ---

if __name__ == "__main__":
    # 假设文件结构与之前相同
    # my_project/
    # ├── base.json             (没有 inherits)
    # ├── components/
    # │   ├── button.json         (inherits: "base")
    # │   ├── special_button.json (inherits: "button")
    # │   └── text_input.json   (inherits: "base")
    # └── other_stuff/
    #     └── config.txt

    target_folder = 'C:/Users/Snapmaker\AppData\Roaming\Snapmaker_Orca\system\Snapmaker\machine'

    # 使用新函数创建映射表
    result_map = create_inheritance_map_v2(target_folder)

    # 打印最终结果
    print("\n--- 继承关系映射表 (包含无继承项) ---")
    # json.dumps 会将 Python 的 None 转换成 JSON 的 null
    print(json.dumps(result_map, indent=2, sort_keys=True))