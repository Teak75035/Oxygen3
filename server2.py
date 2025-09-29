# ---- 导入必要的库 ----
import numpy as np
import requests
import random as r
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from matplotlib import pyplot as plt
import hashlib

# ---- 版本信息 ----
version = "3.1.25-beta_flowerme"

# ---- 参数配置 ----
base_punish = 0.1  # 基础惩罚值
punish_growth = 0.02  # 惩罚增长率
alpha = 0.6  # 权重计算的指数参数
cooldown_rounds = 20  # 冷却回合数

# ---- 全局变量 ----
name_in_file = []  # 成员姓名列表
time_in_file = []  # 成员出场次数列表
cooldown = []  # 冷却状态列表
id = 0  # 当前抽选的成员 ID
final_name = ''  # 最终抽选的成员姓名

# --- 定义路由信息 ---
app = Flask(__name__)
CORS(app)  # 自动添加 CORS 头
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

# ---- 函数部分 ----
def notification(title: str, title_duration: int, title_voice: str,
                 content: str, content_duration: int, content_voice: str):
    """
    发送通知到 Island 插件。
    :param title: 通知标题
    :param title_duration: 标题显示时长（秒）
    :param title_voice: 标题语音内容
    :param content: 通知内容
    :param content_duration: 内容显示时长（秒）
    :param content_voice: 内容语音内容
    """
    url = "http://127.0.0.1:5002/api/notify"  # 请确保与 Island 插件地址相符
    data = {
        "title": title,
        "title_duration": title_duration,
        "title_voice": title_voice,
        "content": content,
        "content_duration": content_duration,
        "content_voice": content_voice
    }

    response = requests.post(url, json=data)
    print("[Server2] Status Code:", response.status_code)
    print("[Server2] Response Body:", response.text)

def read_file():
    """
    从文件中读取成员姓名和出场次数，初始化全局变量 name_in_file、time_in_file 和 cooldown。
    """
    global name_in_file, time_in_file, cooldown
    name_in_file.clear()
    time_in_file.clear()
    cooldown.clear()
    if not os.path.exists('std.namesbook'):
        print("[Server2] ⚠️ 文件 std.namesbook 不存在。")
        return
    with open('std.namesbook', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                name, count = parts[0], parts[1]
                try:
                    name_in_file.append(name)
                    time_in_file.append(int(count))
                    cooldown.append(0)
                except ValueError:
                    print(f"[Server2] namesbook 中出现格式错误的 time ，我们已跳过 Line.{count}")

def weighted_draw(exclude_ids=None, idx=None):
    """
    根据成员的出场次数和冷却状态，进行加权抽选。
    :param exclude_ids: 排除的成员 ID 列表
    :param idx: 当前请求的成员 ID（用于冷却时间的计算）
    :return: 如果是冷却中的成员，返回惩罚分数；否则返回 None
    """
    global id, final_name, cooldown

    exclude_ids = exclude_ids or set()

    if not time_in_file or not name_in_file:
        print("[Server2] ⚠️ namesbook 为空，请检查文件。")
        return

    # 计算惩罚参数和分数上限
    diff = max(time_in_file) - min(time_in_file)
    punish = base_punish + punish_growth * diff
    limit = max(time_in_file) + 1

    # 计算每个成员的分数
    scores = [
        (limit - count) ** alpha if cooldown[i] == 0 and i not in exclude_ids else 0
        for i, count in enumerate(time_in_file)
    ]

    # 如果所有分数为 0，重置冷却状态并重新计算分数
    if not any(scores):
        print("[Server2] ⚠️ 所有成员都处于冷却中或已被排除，重置冷却状态。")
        cooldown = [0] * len(cooldown)
        scores = [
            (limit - count) ** alpha if i not in exclude_ids else 0
            for i, count in enumerate(time_in_file)
        ]

    # 计算权重
    weights = np.exp(np.array(scores) * punish)
    weights_sum = weights.sum()

    if weights_sum == 0:
        print("[Server2] ⚠️ 无可用抽选成员。")
        final_name = ''
        return

    # 归一化权重并进行抽选
    weights /= weights_sum
    id = np.random.choice(range(len(name_in_file)), p=weights)
    final_name = name_in_file[id]

    # 如果提供了 idx 参数，计算并返回惩罚分数
    if idx is not None:
        if cooldown[idx - 1] > 0:
            return 0
        return (limit - time_in_file[idx - 1]) ** alpha * punish

def pushback():
    """
    将当前抽选的成员的出场次数 +1，并更新冷却状态。
    """
    global time_in_file, id, name_in_file, cooldown
    if id is None or not (0 <= id < len(time_in_file)):
        print(f"[Server2] ⚠️ 无效 ID，回溯失败。结果可能受到影响。")
        return

    time_in_file[id] += 1
    cooldown[id] = cooldown_rounds

    try:
        with open('std.namesbook', 'w', encoding='utf-8') as f:
            for name, count in zip(name_in_file, time_in_file):
                f.write(f"{name} {count}\n")
        print(f"[Server2] ✅ 回溯：{name_in_file[id]} 的出场次数 +1，并已写回文件。")
    except Exception as e:
        print(f"[Server2] ❌ 写入文件失败：{e}")

def reset():
    """
    重置所有成员的出场次数和冷却状态。
    """
    read_file()
    global name_in_file, time_in_file, cooldown
    for i in range(len(time_in_file)):
        time_in_file[i] = 0
        cooldown[i] = 0
    with open('std.namesbook', 'w', encoding='utf-8') as f:
        for i in range(len(name_in_file)):
            f.write(f"{name_in_file[i]} 0\n")
    print("[Server2] ✅ namesbook 已重置为初始状态。")

def cooldown_tick():
    """
    冷却时间递减，已冷却的成员将冷却时间减 1。
    """
    global cooldown
    # 使用列表推导式优化冷却状态更新逻辑
    cooldown = [max(0, c - 1) for c in cooldown]

def check_connection():
    """
    向 ClassIsland 发送启动成功的通知，以测试程序与 Island 插件的连接状态。
    """
    notification("IslandCaller NEXT 启动成功", 3, "", "ICNEXT v"+str(version)+" 已成功连接到您的ClassIsland。", 5, "")

def welcome():
    """
    发送欢迎使用的通知。
    """
    print("[Server2] IslandCaller NEXT - 随机进化")
    print("[Server2] 欢迎使用ICNEXT！\n[Server2] 请确保ICNEXT与ClassIsland正在以管理员身份运行，更多帮助请自行查阅程序源码。")
    print(f"[Server2] 版本号 {version} 源码作者 Github @Teak75035")

# ---- 路由部分 ----

@app.route('/rna', methods=['GET'])
def rna():
    """
    根据请求参数 pcs 和 seed，进行成员抽选。
    :return: JSON格式的抽选结果
    """
    global cooldown

    pcs = int(request.args.get('pcs', 1))
    seed = int(request.args.get('seed', r.randint(1, 1000000)))

    if pcs < 1:
        return jsonify({'error': 'pcs 参数必须大于等于 1'}), 400

    read_file()
    r.seed(seed)
    np.random.seed(seed)

    ok_name = []  # 存储本次抽选成功的成员
    used_ids = set()  # 存储已抽选的成员 ID，避免重复抽选

    while len(ok_name) < pcs:
        # 获取可用的成员 ID 列表
        available_ids = [i for i in range(len(name_in_file)) if cooldown[i] == 0 and i not in used_ids]

        if not available_ids:
            print("[Server2] 🌀 无可用抽选对象，重置冷却状态。")
            cooldown = [0] * len(cooldown)
            available_ids = [i for i in range(len(name_in_file)) if i not in used_ids]

            if not available_ids:
                print("[Server2] ⚠️ 无法满足 pcs 数量，名单已耗尽。")
                break

        # 加权抽选成员
        weighted_draw(exclude_ids=used_ids)
        if final_name and id not in used_ids:
            ok_name.append(final_name)
            used_ids.add(id)
            pushback()  # 更新抽选成员的出场次数
        cooldown_tick()  # 更新冷却状态

    return jsonify({
        'code': '200',
        'status': 'success',
        'data': {
            'name': ok_name,
            'seed': seed,
            'pcs': pcs,
        }
    })

@app.route('/resetnamesbook', methods=['GET'])
def reset_namesbook():
    """
    重置所有成员的出场次数和冷却状态。
    :return: JSON格式的操作结果
    """
    key_shadow = str(request.args.get('key', '0'))
    # 使用 SHA256 和 MD5 组合加密
    md5_hash = hashlib.md5(key_shadow.encode('utf-8')).hexdigest()

    if md5_hash != '71b72a4634334ae3b09c14d6761d288b':  # 密码 lingxianww 的 SHA256+MD5 哈希值
        return jsonify({'403': '', 'error': '密钥错误，无法执行重置操作。'}), 403
    else:
        reset()
        return jsonify({
            '200': '',
            'code': '200',
            'status': 'success',
            'message': 'namesbook 已重置为初始状态。'
        }), 200

@app.route('/check', methods=['GET'])
def check():
    """
    查看成员的出场次数和权重信息。
    :return: JSON格式的成员信息
    """
    read_file()
    num = int(request.args.get('id', 0)) - 1
    if num == -1:
        return jsonify({
            'code': '200',
            'status': 'success',
            'data': {
                'names': name_in_file,
                'times': time_in_file,
            }
        })
    elif num < -1 or num >= len(name_in_file):
        return jsonify({'error': 'id 参数无效'}), 400
    else:
        weighted_draw()
        return jsonify({
            'code': '200',
            'status': 'success',
            'data': {
                'name': name_in_file[num],
                'time': time_in_file[num],
                'weight': weighted_draw(num + 1)
            }
        })

@app.route('/less', methods=['GET'])
def less():
    """
    获取出场次数最少的成员及其出场次数。
    :return: JSON格式的成员信息
    """
    max = 10**10
    name = ''
    with open('std.namesbook', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                if parts[1].isdigit():
                    count = int(parts[1])
                    if count <= max:
                        max = int(parts[1])
                        name = parts[0]
    return jsonify({
        'code': '200',
        'status': 'success',
        'data': {
            'name': name,
            'time': max
                }
                    })

@app.route('/status', methods=['GET'])
def status():
    """
    获取当前服务的状态信息，包括版权信息、版本号和作者信息。
    :return: JSON格式的状态信息
    """
    return jsonify({
        'code': '200',
        'status': 'success',
        'data': {
            'copyright': 'lingxianww © 2025-2027',
            'version': version,
            'author': 'lingxianww'
        }
    })

@app.route('/msg', methods=['GET'])           
def msg():
    """
    接收前端或调用方的消息提醒请求，参数包括标题、内容及其持续时间等。
    :return: 返回 empty.html 页面
    """
    title = str(request.args.get('title', '通知'))
    title_duration = int(request.args.get('title_duration', 3))
    title_voice = str(request.args.get('title_voice', ''))
    content = str(request.args.get('content', ''))
    content_duration = int(request.args.get('content_duration', 0))
    content_voice = str(request.args.get('content_voice', ''))
    notification(title, title_duration, title_voice, content, content_duration, content_voice)
    
    # 返回 empty.html 页面
    return send_file('empty.html')

@app.route('/chart', methods=['GET'])
def chart():
    """
    生成并返回成员出场次数的统计图。
    :return: 返回生成的统计图像文件
    """
    read_file()
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置字体为微软雅黑
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.figure(figsize=(10, 6))
    plt.bar(name_in_file, time_in_file, color='skyblue')
    plt.xlabel('姓名')
    plt.ylabel('出场次数')
    plt.title('成员出场次数统计')
    plt.xticks(rotation=90, ha='right')
    img_path = 'static/attendance.png'
    os.makedirs('static', exist_ok=True)
    plt.savefig(img_path)
    with open(img_path, 'rb') as img_file:
        img_data = img_file.read()
    return img_data, 200, {
        'Content-Type': 'image/png',
        'Content-Disposition': 'inline; filename="attendance.png"'
    }

@app.route('/rnafromweb', methods=['GET'])
def rna_from_web():
    """
    从网页请求中获取抽选参数 pcs 和 seed，进行成员抽选，并发送通知。
    :return: empty.html 页面
    """
    global cooldown

    pcs = int(request.args.get('pcs', 1))
    seed = int(request.args.get('seed', r.randint(1, 1000000)))

    if pcs < 1:
        return jsonify({'error': 'pcs 参数必须大于等于 1'}), 400

    read_file()
    r.seed(seed)
    np.random.seed(seed)

    ok_name = []
    used_ids = set()

    while len(ok_name) < pcs:
        available_ids = [i for i in range(len(name_in_file)) if cooldown[i] == 0 and i not in used_ids]

        if not available_ids:
            print("[Server2] 🌀 无可用抽选对象，重置冷却状态。")
            cooldown = [0] * len(cooldown)
            available_ids = [i for i in range(len(name_in_file)) if i not in used_ids]

            if not available_ids:
                print("[Server2] ⚠️ 无法满足 pcs 数量，名单已耗尽。")
                break

        weighted_draw(exclude_ids=used_ids)
        if final_name and id not in used_ids:
            ok_name.append(final_name)
            used_ids.add(id)
            pushback()
        cooldown_tick()

    notification("批量抽取结果", 2, "", f"{ok_name}", 10, "")
    
    return send_file('empty.html')
    
@app.route('/msghelp', methods=['GET'])
def msghelp():
    # 返回消息提醒参数的说明，供前端或调用方参考
    return jsonify({
        "title": "提醒标题",  # 通知栏标题
        "title_duration": "这是提醒标题的持续时间",  # 标题显示时长（秒）
        "title_voice": "这是语音播放的提醒标题",  # 标题语音内容
        "content": "提醒内容",  # 通知栏内容
        "content_duration": "这是提醒内容的持续时间",  # 内容显示时长（秒）
        "content_voice": "这是语音播放的提醒内容"  # 内容语音内容
    })

@app.route('/kill', methods=['GET'])
def kill():
    """
    终止所有 Python 进程。
    Windows 平台使用 taskkill 命令，其他平台使用 pkill。
    """
   
    if os.name == 'nt':  # Windows 系统
        os.system("taskkill /F /IM python.exe /T")  # 强制终止所有 Python 进程
    else:  # 其他系统（如 Linux、macOS）
        os.system("pkill -f python")  # 终止所有 Python 进程
    return jsonify({
            '200': '',
            'code': '200',
            'status': 'success',
            'message': '所有 Python 进程已被终止。'
        }), 200

# ---- 程序部分 ----

if __name__ == '__main__':
    welcome()
    check_connection()
    app.run(host='0.0.0.0', port=5001)

########如果端口冲突，请同时修改本程序和hower.py！（默认5001）########

