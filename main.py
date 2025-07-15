from flask import Flask, request, render_template_string
import os, requests, time, random, string, json, atexit
from threading import Thread, Event

app = Flask(__name__)
app.secret_key = 'BROKEN_SECRET_KEY'
app.debug = True

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': '/',
    'Accept-Language': 'en-US,en;q=0.9',
}

stop_events, threads, active_users = {}, {}, {}
TASK_FILE = 'tasks.json'

def save_tasks():
    with open(TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump(active_users, f, ensure_ascii=False, indent=2)

def load_tasks():
    if not os.path.exists(TASK_FILE): return
    with open(TASK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for tid, info in data.items():
            active_users[tid] = info
            stop_events[tid] = Event()
            if info.get('status') == 'ACTIVE':
                if not info.get('fb_name'):
                    info['fb_name'] = fetch_profile_name(info['token'])
                th = Thread(
                    target=send_messages,
                    args=(
                        info['tokens_all'],
                        info['thread_id'],
                        info['name'],
                        info.get('delay', 1),
                        info['msgs'],
                        tid
                    ),
                    daemon=True
                )
                th.start()
                threads[tid] = th

atexit.register(save_tasks)
load_tasks()

def fetch_profile_name(token: str) -> str:
    try:
        res = requests.get(
            f'https://graph.facebook.com/me?access_token={token}',
            timeout=8
        )
        return res.json().get('name', 'Unknown')
    except Exception:
        return 'Unknown'

def send_messages(tokens, thread_id, mn, delay, messages, task_id):
    ev = stop_events[task_id]
    tok_i, msg_i = 0, 0
    total_tok, total_msg = len(tokens), len(messages)
    while not ev.is_set():
        tk = tokens[tok_i]
        msg = messages[msg_i]
        try:
            requests.post(
                f'https://graph.facebook.com/v15.0/t_{thread_id}/',
                data={'access_token': tk, 'message': f"{mn} {msg}"},
                headers=headers,
                timeout=10
            )
            print(f"[✔️ SENT] {msg[:40]} via TOKEN-{tok_i+1}")
        except Exception as e:
            print("[⚠️ ERROR]", e)
        tok_i = (tok_i + 1) % total_tok
        msg_i = (msg_i + 1) % total_msg
        time.sleep(delay)

@app.route('/', methods=['GET', 'POST'])
def home():
    msg_html = stop_html = ""
    if request.method == 'POST':
        if 'txtFile' in request.files:
            tokens = (
                [request.form.get('singleToken').strip()]
                if request.form.get('tokenOption') == 'single'
                else request.files['tokenFile'].read()
                .decode(errors='ignore')
                .splitlines()
            )
            tokens = [t for t in tokens if t]
            uid = request.form.get('threadId','').strip()
            hater = request.form.get('kidx','').strip()
            delay = max(int(request.form.get('time',1) or 1),1)
            file = request.files['txtFile']
            msgs = [m for m in file.read().decode(errors='ignore').splitlines() if m]
            if not (tokens and uid and hater and msgs):
                msg_html = "<div class='alert alert-danger rounded-pill p-2'>⚠️ All fields required!</div>"
            else:
                tid = 'brokennadeem' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                stop_events[tid] = Event()
                th = Thread(
                    target=send_messages,
                    args=(tokens, uid, hater, delay, msgs, tid),
                    daemon=True
                )
                th.start()
                threads[tid] = th
                active_users[tid] = {
                    'name': hater,
                    'token': tokens[0],
                    'tokens_all': tokens,
                    'fb_name': fetch_profile_name(tokens[0]),
                    'thread_id': uid,
                    'msg_file': file.filename or 'messages.txt',
                    'msgs': msgs,
                    'delay': delay,
                    'msg_count': len(msgs),
                    'status': 'ACTIVE'
                }
                save_tasks()
                msg_html = f"<div class='stop-key rounded-pill p-3'>🔑 <b>STOP KEY↷</b><br><code>{tid}</code></div>"
        elif 'taskId' in request.form:
            tid = request.form.get('taskId','').strip()
            if tid in stop_events:
                stop_events[tid].set()
                if tid in active_users:
                    active_users[tid]['status'] = 'OFFLINE'
                save_tasks()
                stop_html = "<div class='stop-ok rounded-pill p-3'>⏹️ <b>STOPPED</b><br><code>{}</code></div>".format(tid)
            else:
                stop_html = "<div class='stop-bad rounded-pill p-3'>❌ <b>INVALID KEY</b><br><code>{}</code></div>".format(tid)
    return render_template_string(html_template, msg_html=msg_html, stop_html=stop_html)

html_template = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>⚔️ 𝐀𝐋𝐎𝐍𝐄 𝐊𝐑𝐈𝐗 ⚔️</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: start;
      padding-top: 0;
      margin-top: 0;
      color: #fff;
      font-family: 'Poppins', sans-serif;
      background: linear-gradient(45deg,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#4b0082,#8f00ff);
      background-size: 600% 600%;
      animation: rainbowMove 18s ease infinite;
    }
    @keyframes rainbowMove {
      0% {background-position: 0% 50%}
      50% {background-position: 100% 50%}
      100% {background-position: 0% 50%}
    }
    .card-dark {
      background: rgba(0,0,0,0.65);
      border: 2px solid yellow;
      border-radius: 2rem;
      padding: 1.5rem;
      margin-top: 0;
    }
    .card-dark input, .card-dark select {
      border-radius: 2rem;
    }
    .card-dark .btn {
      border-radius: 2rem;
      padding: 0.4rem 2.5rem;
      font-size: 1.1rem;
    }
    .stop-key, .stop-ok, .stop-bad {
      margin-top: 1.5rem;
      border-radius: 2rem;
      border: 2px solid yellow;
      text-align: center;
      font-size: 1.1rem;
    }
    .stop-key {background:black; color:red;}
    .stop-ok {background:darkred; color:red;}
    .stop-bad {background:gray; color:black;}
  </style>
  <script>
    function toggleTokenOption(type) {
      document.getElementById('singleTokenDiv').style.display = (type==='single')?'block':'none';
      document.getElementById('tokenFileDiv').style.display = (type==='file')?'block':'none';
    }
  </script>
</head>
<body>
  <div class="container p-0">
    <div class="card-dark w-100">
      <h2 class="text-center">⚔️ 𝗔⃪𝗟⃪𝗢⃪𝗡⃪𝗘⃪ 𝗩⃪𝗜⃪𝗕⃪𝗘⃪𝗥⃪ 𝗕⃪𝗢⃪𝗜⃪𝗜⃪ 𝐆𝐀𝐁𝐁𝐀𝐑 𝐗 𝐊𝐑𝐈𝐗 𝗜⃪𝗡⃪𝗫⃪𝗜⃪𝗗⃪𝗘⃪ ⚔️</h2>
      <form method="POST" enctype="multipart/form-data">
        <div class="mb-3">
          <label class="form-label">TOKEN OPTION</label><br>
          <input type="radio" name="tokenOption" value="single" checked onclick="toggleTokenOption('single')"> Single &nbsp;
          <input type="radio" name="tokenOption" value="file" onclick="toggleTokenOption('file')"> File
        </div>
        <div id="singleTokenDiv" class="mb-3">
          <label class="form-label">Enter Single Token</label>
          <input type="text" name="singleToken" class="form-control" placeholder="Enter single token">
        </div>
        <div id="tokenFileDiv" style="display:none" class="mb-3">
          <label class="form-label">Upload Token File</label>
          <input type="file" name="tokenFile" class="form-control" accept=".txt">
        </div>
        <div class="mb-3">
          <label class="form-label">Conversation ID</label>
          <input type="text" name="threadId" class="form-control" placeholder="Conversation ID" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Hater Name</label>
          <input type="text" name="kidx" class="form-control" placeholder="Hater Name" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Speed (in seconds)</label>
          <input type="number" name="time" class="form-control" placeholder="Speed (seconds)" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Message File (.txt)</label>
          <input type="file" name="txtFile" class="form-control" accept=".txt" required>
        </div>
        <div class="text-center mb-4">
          <button type="submit" class="btn btn-success">🚀 START LODER</button>
        </div>
      </form>
      {{msg_html|safe}}
      <hr>
      <form method="POST">
        <div class="mb-3">
          <label class="form-label">Enter STOP KEY</label>
          <input type="text" name="taskId" class="form-control" placeholder="Enter STOP KEY" required>
        </div>
        <div class="text-center">
          <button type="submit" class="btn btn-danger">⛔ STOP LODER</button>
        </div>
      </form>
      {{stop_html|safe}}
    </div>
  </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
