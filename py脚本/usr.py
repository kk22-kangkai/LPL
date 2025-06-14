import json
from collections import Counter, defaultdict
from datetime import datetime
import os


def generate_report(json_file_path="D:\code\LPL\py脚本\output.json", output_html_path="ticket_analysis_report.html"):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件 '{json_file_path}' 未找到。请确保文件存在于正确的位置。")
        return
    except json.JSONDecodeError:
        print(f"错误: 文件 '{json_file_path}' 不是有效的JSON格式。")
        return

    # 1. 按状态统计工单数量
    status_counts = Counter(ticket['local_status'] for ticket in data)

    # 2. 按评分统计工单数量
    score_counts = Counter(ticket['local_score'] for ticket in data)

    # 3. 每月创建的工单数量
    created_per_month = defaultdict(int)
    for ticket in data:
        try:
            # 确保 created_at 字段存在且不为空
            if ticket.get('created_at'):
                dt = datetime.strptime(ticket['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                created_per_month[dt.strftime("%Y-%m")] += 1
        except (ValueError, TypeError) as e:
            print(
                f"警告: 工单 {ticket.get('ticket_id')} 的 created_at 格式无效或缺失: {ticket.get('created_at')}. Error: {e}")
            continue  # 跳过这个工单的日期处理

    sorted_months = sorted(created_per_month.keys())
    month_labels = list(sorted_months)
    month_values = [created_per_month[m] for m in sorted_months]

    # 4. 平均首次解决时间和平均完全解决时间 (仅针对已解决的工单)
    solved_tickets_resolution = [
        ticket for ticket in data
        if ticket.get('solved_at') and ticket.get('first_resolution_time_in_minutes') is not None
    ]

    first_res_times = [t['first_resolution_time_in_minutes'] for t in solved_tickets_resolution]
    full_res_times = [t['full_resolution_time_in_minutes'] for t in solved_tickets_resolution if
                      t.get('full_resolution_time_in_minutes') is not None]

    avg_first_res = sum(first_res_times) / len(first_res_times) if first_res_times else 0
    avg_full_res = sum(full_res_times) / len(full_res_times) if full_res_times else 0

    # 5. 工单重开次数分布
    reopen_counts = Counter(ticket.get('reopens', 0) for ticket in data)  # 使用 .get 提供默认值0
    # 为了图表美观，可以考虑合并较高的重开次数
    processed_reopen_counts = defaultdict(int)
    for reopens, count in reopen_counts.items():
        if reopens >= 3:  # 将3次及以上的重开合并
            processed_reopen_counts['3+'] += count
        else:
            processed_reopen_counts[str(reopens)] += count
    reopen_labels = sorted(processed_reopen_counts.keys(),
                           key=lambda x: int(x.replace('+', '')) if x.endswith('+') else int(x))
    reopen_values = [processed_reopen_counts[k] for k in reopen_labels]

    # 6. 工单回复次数分布
    replies_counts = Counter(ticket.get('replies', 0) for ticket in data)
    # 为了图表美观，可以考虑合并较高的回复次数或分组
    replies_dist = defaultdict(int)
    for replies, count in replies_counts.items():
        if replies == 0:
            replies_dist['0 replies'] += count
        elif 1 <= replies <= 3:
            replies_dist['1-3 replies'] += count
        elif 4 <= replies <= 7:
            replies_dist['4-7 replies'] += count
        elif 8 <= replies <= 10:
            replies_dist['8-10 replies'] += count
        else:  # replies > 10
            replies_dist['10+ replies'] += count

    reply_dist_labels = ['0 replies', '1-3 replies', '4-7 replies', '8-10 replies', '10+ replies']
    reply_dist_values = [replies_dist[k] for k in reply_dist_labels]

    # 7. 平均请求者等待时间 (仅针对已解决或有等待时间的工单)
    tickets_with_wait_time = [
        ticket for ticket in data
        if ticket.get('requester_wait_time_in_minutes') is not None
    ]
    wait_times = [t['requester_wait_time_in_minutes'] for t in tickets_with_wait_time]
    avg_requester_wait = sum(wait_times) / len(wait_times) if wait_times else 0

    # 生成HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>工单数据分析报告</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: #f4f7f6; color: #333; }}
            .container {{ max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #fff; box-shadow: 0 0 15px rgba(0,0,0,0.1); border-radius: 8px; }}
            h1 {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #7f8c8d; padding-bottom: 10px; margin-top: 40px; }}
            .grid-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
                margin-bottom: 30px;
            }}
            .chart-container {{
                padding: 20px;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }}
            .full-width-chart {{
                grid-column: 1 / -1; /* 使图表占据整行 */
            }}
            canvas {{ width: 100% !important; height: auto !important; max-height: 400px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>工单数据分析报告</h1>

            <div class="grid-container">
                <div class="chart-container">
                    <h2>工单状态分布</h2>
                    <canvas id="statusChart"></canvas>
                </div>
                <div class="chart-container">
                    <h2>工单评分分布</h2>
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>

            <div class="grid-container">
                 <div class="chart-container full-width-chart">
                    <h2>每月创建工单数量</h2>
                    <canvas id="createdPerMonthChart"></canvas>
                </div>
            </div>

            <div class="grid-container">
                <div class="chart-container">
                    <h2>平均解决时间 (分钟)</h2>
                    <p>(仅统计已解决的工单)</p>
                    <canvas id="avgResolutionChart"></canvas>
                </div>
                <div class="chart-container">
                    <h2>工单重开次数分布</h2>
                    <canvas id="reopensChart"></canvas>
                </div>
            </div>

            <div class="grid-container">
                <div class="chart-container">
                    <h2>工单回复次数分布</h2>
                    <canvas id="repliesChart"></canvas>
                </div>
                <div class="chart-container">
                    <h2>平均请求者等待时间 (分钟)</h2>
                     <p>(统计所有有等待时间的工单)</p>
                    <canvas id="avgWaitTimeChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            const pieColors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF'];
            const barColors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];

            // 1. 状态图表 (饼图)
            new Chart(document.getElementById('statusChart'), {{
                type: 'pie',
                data: {{
                    labels: {list(status_counts.keys())},
                    datasets: [{{
                        label: '工单状态',
                        data: {list(status_counts.values())},
                        backgroundColor: pieColors.slice(0, {len(status_counts)})
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            // 2. 评分图表 (甜甜圈图)
            new Chart(document.getElementById('scoreChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {list(score_counts.keys())},
                    datasets: [{{
                        label: '工单评分',
                        data: {list(score_counts.values())},
                        backgroundColor: pieColors.slice(0, {len(score_counts)})
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});

            // 3. 每月创建工单数量 (折线图)
            new Chart(document.getElementById('createdPerMonthChart'), {{
                type: 'line',
                data: {{
                    labels: {month_labels},
                    datasets: [{{
                        label: '创建的工单数',
                        data: {month_values},
                        borderColor: '#36A2EB',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});

            // 4. 平均解决时间 (柱状图)
            new Chart(document.getElementById('avgResolutionChart'), {{
                type: 'bar',
                data: {{
                    labels: ['平均首次解决时间', '平均完全解决时间'],
                    datasets: [{{
                        label: '分钟',
                        data: [{avg_first_res:.2f}, {avg_full_res:.2f}],
                        backgroundColor: [barColors[0], barColors[1]]
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: '分钟' }} }} }}
                }}
            }});

            // 5. 重开次数分布 (柱状图)
            new Chart(document.getElementById('reopensChart'), {{
                type: 'bar',
                data: {{
                    labels: {reopen_labels},
                    datasets: [{{
                        label: '工单数量',
                        data: {reopen_values},
                        backgroundColor: barColors.slice(0, {len(reopen_labels)})
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: '工单数量' }} }},
                        x: {{ title: {{ display: true, text: '重开次数' }} }}
                    }}
                }}
            }});

            // 6. 回复次数分布 (柱状图)
            new Chart(document.getElementById('repliesChart'), {{
                type: 'bar',
                data: {{
                    labels: {reply_dist_labels},
                    datasets: [{{
                        label: '工单数量',
                        data: {reply_dist_values},
                        backgroundColor: barColors.slice(0, {len(reply_dist_labels)})
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true, title: {{ display: true, text: '工单数量' }} }},
                        x: {{ title: {{ display: true, text: '回复次数区间' }} }}
                    }}
                }}
            }});

            // 7. 平均请求者等待时间 (单个值的柱状图)
            new Chart(document.getElementById('avgWaitTimeChart'), {{
                type: 'bar',
                data: {{
                    labels: ['平均等待时间'],
                    datasets: [{{
                        label: '分钟',
                        data: [{avg_requester_wait:.2f}],
                        backgroundColor: [barColors[2]]
                    }}]
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: '分钟' }} }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    try:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"报告已生成: {os.path.abspath(output_html_path)}")
    except IOError:
        print(f"错误: 无法写入HTML文件到 '{output_html_path}'。")


if __name__ == '__main__':
    # 你可以将json文件名和输出html文件名作为参数传递
    # 例如: generate_report("my_tickets.json", "my_report.html")
    generate_report()