import json


# ==============================================================================
# 1. 数据结构和树的构建逻辑 (与之前相同)
# ==============================================================================
class TreeNode:
    """定义一个简单的树节点类"""

    def __init__(self, name):
        self.name = name
        self.children = []

    def __repr__(self):
        return f"TreeNode({self.name})"


def build_forest(inheritance_map: dict) -> list:
    """根据继承关系映射表构建一个森林（多棵树的列表）。"""
    nodes = {}

    for name in inheritance_map.keys():
        nodes[name] = TreeNode(name)

    roots = []
    for name, parent_name in inheritance_map.items():
        current_node = nodes.get(name)
        if current_node is None: continue  # Should not happen if data is consistent

        if parent_name is None:
            roots.append(current_node)
        else:
            if parent_name not in nodes:
                nodes[parent_name] = TreeNode(parent_name)

            parent_node = nodes[parent_name]
            parent_node.children.append(current_node)

    return roots


# ==============================================================================
# 2. HTML 生成逻辑
# ==============================================================================

def generate_html_for_node(node: TreeNode) -> str:
    """递归地为单个节点及其子节点生成 HTML 列表项。"""
    html = "<li>"
    if node.children:
        # 如果有子节点，添加一个可点击的箭头
        html += '<span class="caret"></span>'
        html += f'<span class="node-name">{node.name}</span>'
        # 为子节点创建一个嵌套列表
        html += '<ul class="nested">'
        for child in node.children:
            html += generate_html_for_node(child)
        html += '</ul>'
    else:
        # 如果是叶子节点，则不加箭头
        html += f'<span class="node-name leaf">{node.name}</span>'
    html += "</li>"
    return html


def create_html_page(roots: list, title: str) -> str:
    """创建完整的、自包含的 HTML 页面字符串。"""

    # --- CSS 样式 ---
    css_styles = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
        h1 { color: #343a40; }
        ul { list-style-type: none; padding-left: 20px; }
        .caret {
            cursor: pointer;
            user-select: none; /* 防止双击时选中文本 */
            display: inline-block;
            margin-right: 6px;
        }
        .caret::before {
            content: "►"; /* 折叠时的箭头 */
            color: #6c757d;
            display: inline-block;
            transition: transform 0.1s ease-in-out;
        }
        .caret-down::before {
            transform: rotate(90deg); /* 展开时的箭头 */
        }
        .nested {
            display: none; /* 默认隐藏子树 */
        }
        .active {
            display: block; /* 点击后显示子树 */
        }
        .node-name { font-size: 16px; color: #212529; }
        .node-name.leaf { margin-left: 18px; color: #495057; }
        li { padding: 4px 0; }
    </style>
    """

    # --- JavaScript 逻辑 ---
    js_script = """
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            var toggler = document.getElementsByClassName("caret");
            for (var i = 0; i < toggler.length; i++) {
                toggler[i].addEventListener("click", function() {
                    // 切换箭头的方向
                    this.classList.toggle("caret-down");

                    // 找到嵌套的 ul 列表并切换其显示状态
                    var nested = this.parentElement.querySelector(".nested");
                    if (nested) {
                        nested.classList.toggle("active");
                    }
                });
            }
        });
    </script>
    """

    # --- HTML 主体内容 ---
    body_content = ""
    for root in roots:
        body_content += generate_html_for_node(root)

    # --- 整合所有部分 ---
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        {css_styles}
    </head>
    <body>
        <h1>{title}</h1>
        <ul id="treeRoot">
            {body_content}
        </ul>
        {js_script}
    </body>
    </html>
    """
    return html_template


# ==============================================================================
# 3. 主程序
# ==============================================================================
if __name__ == "__main__":
    # 您提供的原始数据
    with open("tree.json", "r", encoding="utf-8") as f:
        inheritance_data=json.loads(f.read())
    forest_roots = build_forest(inheritance_data)

    # 2. 生成完整的 HTML 页面内容
    page_title = "继承结构可视化"
    html_output = create_html_page(forest_roots, page_title)

    # 3. 将内容写入文件
    output_filename = "tree_visualization.html"
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"✅ 成功生成网页！请在浏览器中打开文件: {output_filename}")
    except Exception as e:
        print(f"❌ 生成文件时出错: {e}")