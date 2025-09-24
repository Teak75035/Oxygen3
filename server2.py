import numpy as np
import requests
import random as r
from flask import Flask, request, jsonify
import os

# ---- 版本信息 ----
version = "3.1.12"

# ---- 参数配置 ----
base_punish = 0.1
punish_growth = 0.02
alpha = 0.6
cooldown_rounds = 20

# ---- 全局变量 ----
o_name = []
o_time = []
cooldown = []
id = 0
final_name = ''

# --- 定义路由信息 ---
app = Flask(__name__)

# ---- 函数部分 ----
def notification(title: str, title_duration: int, title_voice: str,
                 content: str, content_duration: int, content_voice: str):
    url = "http://127.0.0.1:5002/api/notify" ########请确保与Island插件地址相符！
    data = {
        "title": title,
        "title_duration": title_duration,
        "title_voice": title_voice,
        "content": content,
        "content_duration": content_duration,
        "content_voice": content_voice
    }

    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)

def read_file():
    global o_name, o_time, cooldown
    o_name.clear()
    o_time.clear()
    cooldown.clear()
    if not os.path.exists('std.namesbook'):
        print("⚠️ 文件 std.namesbook 不存在。")
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
                    print(f"namesbook 中出现格式错误的 time ，我们已跳过 Line.{count}")

def weighted_draw(exclude_ids=None, idx=None):
    global id, final_name, cooldown

    if exclude_ids is None:
        exclude_ids = set()

    if not o_time or not o_name:
        print("⚠️ namesbook 为空，请检查文件。")
        return

    diff = max(o_time) - min(o_time)
    punish = base_punish + punish_growth * diff
    limit = max(o_time) + 1

    scores = [
        (limit - count) ** alpha if cooldown[i] == 0 and i not in exclude_ids else 0
        for i, count in enumerate(o_time)
    ]

    if sum(scores) == 0:
        print("⚠️ 所有成员都处于冷却中或已被排除，重置冷却状态。")
        cooldown = [0] * len(cooldown)
        scores = [
            (limit - count) ** alpha if i not in exclude_ids else 0
            for i, count in enumerate(o_time)
        ]

    weights = np.exp(np.array(scores) * punish)
    weights_sum = weights.sum()

    if weights_sum == 0:
        print("⚠️ 无可用抽选成员。")
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
    global o_time, id, o_name, cooldown
    if id is None or not (0 <= id < len(o_time)):
        print(f"⚠️ 无效 ID，回溯失败。结果可能受到影响。")
        return

    o_time[id] += 1
    cooldown[id] = cooldown_rounds

    try:
        with open('std.namesbook', 'w', encoding='utf-8') as f:
            for name, count in zip(o_name, o_time):
                f.write(f"{name} {count}\n")
        print(f"✅ 回溯：{o_name[id]} 的出场次数 +1，并已写回文件。")
    except Exception as e:
        print(f"❌ 写入文件失败：{e}")

def reset():
    read_file()
    global o_name, o_time, cooldown
    for i in range(len(o_time)):
        o_time[i] = 0
        cooldown[i] = 0
    with open('std.namesbook', 'w', encoding='utf-8') as f:
        for i in range(len(o_name)):
            f.write(f"{o_name[i]} 0\n")
    print("✅ namesbook 已重置为初始状态。")

def cooldown_tick():
    global cooldown
    for i in range(len(cooldown)):
        if cooldown[i] > 0:
            cooldown[i] -= 1

'''路由部分↓'''

@app.route('/rna', methods=['GET'])
def rna():
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
            print("🌀 无可用抽选对象，重置冷却状态。")
            cooldown = [0] * len(cooldown)
            available_ids = [i for i in range(len(o_name)) if i not in used_ids]

            if not available_ids:
                print("⚠️ 无法满足 pcs 数量，名单已耗尽。")
                break

        weighted_draw(exclude_ids=used_ids)
        if final_name and id not in used_ids:
            ok_name.append(final_name)
            used_ids.add(id)
            pushback()
        cooldown_tick()

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
    
    reset()
    return jsonify({
        'code': '200',
        'status': 'success',
        'message': 'namesbook 已重置为初始状态。'
        })

@app.route('/see', methods=['GET'])
def see():
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
    title = str(request.args.get('title', '通知'))
    title_duration = int(request.args.get('title_duration', 3))
    title_voice = str(request.args.get('title_voice', ''))
    content = str(request.args.get('content', ''))
    content_duration = int(request.args.get('content_duration', 0))
    content_voice = str(request.args.get('content_voice', ''))
    notification(title, title_duration, title_voice, content, content_duration, content_voice)
    return jsonify({
        'code': '200',
        'status': 'success',
        'message': '通知已发送'
    })
    
@app.route('/msghelp', methods=['GET'])
def msghelp():
    return jsonify(
    {
    "title": "提醒标题",
    "title_duration": "这是提醒标题的持续时间",
    "title_voice": "这是语音播放的提醒标题",
    "content": "提醒内容",
    "content_duration": "这是提醒内容的持续时间",
    "content_voice": "这是语音播放的提醒内容"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
########如果端口冲突，请同时修改本程序和hower.py！（默认5001）########
    print("IslandCaller NEXT - 随机进化")
    print("\n欢迎使用ICNEXT！\n请确保ICNEXT与ClassIsland正在以管理员身份运行，更多帮助请自行查阅程序源码。")
    print("\n源码作者 lingxianww -Github@Teak75035")
