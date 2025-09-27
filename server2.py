# ---- 导入必要的库 ----
import numpy as np
import requests
import random as r
from flask import Flask, request, jsonify, send_file
import os
from matplotlib import pyplot as plt

# ---- 版本信息 ----
version = "3.1.21-beta_flowerme"

# ---- 参数配置 ----
base_punish = 0.1  # 基础惩罚值
punish_growth = 0.02  # 惩罚增长率
alpha = 0.6  # 权重计算的指数参数
cooldown_rounds = 20  # 冷却回合数

# ---- 全局变量 ----
o_name = []  # 成员姓名列表
o_time = []  # 成员出场次数列表
cooldown = []  # 冷却状态列表
id = 0  # 当前抽选的成员 ID
final_name = ''  # 最终抽选的成员姓名

# --- 定义路由信息 ---
app = Flask(__name__)

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
    从文件中读取成员姓名和出场次数，初始化全局变量 o_name、o_time 和 cooldown。
    """
    global o_name, o_time, cooldown
    o_name.clear()
    o_time.clear()
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
                    o_name.append(name)
                    o_time.append(int(count))
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

    if exclude_ids is None:
        exclude_ids = set()

    if not o_time or not o_name:
        print("[Server2] ⚠️ namesbook 为空，请检查文件。")
        return

    diff = max(o_time) - min(o_time)
    punish = base_punish + punish_growth * diff
    limit = max(o_time) + 1

    scores = [
        (limit - count) ** alpha if cooldown[i] == 0 and i not in exclude_ids else 0
        for i, count in enumerate(o_time)
    ]

    if sum(scores) == 0:
        print("[Server2] ⚠️ 所有成员都处于冷却中或已被排除，重置冷却状态。")
        cooldown = [0] * len(cooldown)
        scores = [
            (limit - count) ** alpha if i not in exclude_ids else 0
            for i, count in enumerate(o_time)
        ]

    weights = np.exp(np.array(scores) * punish)
    weights_sum = weights.sum()

    if weights_sum == 0:
        print("[Server2] ⚠️ 无可用抽选成员。")
        final_name = ''
        return

    weights /= weights_sum
    id = np.random.choice(range(len(o_name)), p=weights)
    final_name = o_name[id]

    if idx is not None:
        if cooldown[idx - 1] > 0:
            return 0
        test_score = (limit - o_time[idx - 1]) ** alpha
        return test_score * punish

def pushback():
    """
    将当前抽选的成员的出场次数 +1，并更新冷却状态。
    """
    global o_time, id, o_name, cooldown
    if id is None or not (0 <= id < len(o_time)):
        print(f"[Server2] ⚠️ 无效 ID，回溯失败。结果可能受到影响。")
        return

    o_time[id] += 1
    cooldown[id] = cooldown_rounds

    try:
        with open('std.namesbook', 'w', encoding='utf-8') as f:
            for name, count in zip(o_name, o_time):
                f.write(f"{name} {count}\n")
        print(f"[Server2] ✅ 回溯：{o_name[id]} 的出场次数 +1，并已写回文件。")
    except Exception as e:
        print(f"[Server2] ❌ 写入文件失败：{e}")

def reset():
    """
    重置所有成员的出场次数和冷却状态。
    """
    read_file()
    global o_name, o_time, cooldown
    for i in range(len(o_time)):
        o_time[i] = 0
        cooldown[i] = 0
    with open('std.namesbook', 'w', encoding='utf-8') as f:
        for i in range(len(o_name)):
            f.write(f"{o_name[i]} 0\n")
    print("[Server2] ✅ namesbook 已重置为初始状态。")

def cooldown_tick():
    """
    冷却时间递减，已冷却的成员将冷却时间减 1。
    """
    global cooldown
    for i in range(len(cooldown)):
        if cooldown[i] > 0:
            cooldown[i] -= 1

def check_connection():
    """
    检查与 Island 插件的连接，并发送启动成功的通知。
    """
    notification("IslandCaller NEXT 启动成功", 3, "", "ICNEXT v"+str(version)+" 已成功连接到您的ClassIsland。", 5, "")

'''路由部分↓'''

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
        available_ids = [i for i in range(len(o_name)) if cooldown[i] == 0 and i not in used_ids]

        if not available_ids:
            print("[Server2] 🌀 无可用抽选对象，重置冷却状态。")
            cooldown = [0] * len(cooldown)
            available_ids = [i for i in range(len(o_name)) if i not in used_ids]

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

@app.route('/reset/all', methods=['GET'])
def reset_route():
    """
    重置所有成员的出场次数和冷却状态。
    :return: JSON格式的操作结果
    """
    
    reset()
    return jsonify({
        'code': '200',
        'status': 'success',
        'message': 'namesbook 已重置为初始状态。'
        })

@app.route('/see', methods=['GET'])
def see():
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
                'names': o_name,
                'times': o_time,
            }
        })
    elif num < -1 or num >= len(o_name):
        return jsonify({'error': 'id 参数无效'}), 400
    else:
        weighted_draw()
        return jsonify({
            'code': '200',
            'status': 'success',
            'data': {
                'name': o_name[num],
                'time': o_time[num],
                'weight': weighted_draw(num + 1)
            }
        })

@app.route('/last', methods=['GET'])
def last():
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

@app.route('/pic', methods=['GET'])
def pic():
    """
    生成并返回成员出场次数的统计图。
    :return: 返回生成的统计图像文件
    """
    read_file()
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置字体为微软雅黑
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.figure(figsize=(10, 6))
    plt.bar(o_name, o_time, color='skyblue')
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
def rnafromweb():
    """
    从网页请求中获取抽选参数 pcs 和 seed，进行成员抽选，并发送通知。
    :return: None
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
        available_ids = [i for i in range(len(o_name)) if cooldown[i] == 0 and i not in used_ids]

        if not available_ids:
            print("[Server2] 🌀 无可用抽选对象，重置冷却状态。")
            cooldown = [0] * len(cooldown)
            available_ids = [i for i in range(len(o_name)) if i not in used_ids]

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
    
    return None
    
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

if __name__ == '__main__':
    print("[Server2] IslandCaller NEXT - 随机进化")
    print("[Server2] \n欢迎使用ICNEXT！\n请确保ICNEXT与ClassIsland正在以管理员身份运行，更多帮助请自行查阅程序源码。")
    print("[Server2] \n源码作者 lingxianww -Github@Teak75035")
    check_connection()
    app.run(host='0.0.0.0', port=5001)

########如果端口冲突，请同时修改本程序和hower.py！（默认5001）########

