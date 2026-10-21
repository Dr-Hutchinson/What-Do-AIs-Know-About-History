"""Start, inspect, or stop this project's Streamlit/Pinggy preview."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".preview"
STATE.mkdir(exist_ok=True)

def alive(name):
    path = STATE / (name + ".json")
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    try:
        # Verify process identity before using a saved PID (Linux /proc).
        fields = Path(f"/proc/{record['pid']}/stat").read_text().rsplit(")", 1)[1].split()
        if fields[19] == record['start'] and fields[0] != 'Z':
            return record['pid']
    except (FileNotFoundError, ProcessLookupError):
        pass
    return None

def launch(name, args):
    if alive(name):
        return
    with (STATE / (name + ".log")).open("w") as log:
        env = os.environ.copy()
        for key in ('GH_TOKEN', 'OPENAI_API_KEY', 'GITHUB_TOKEN'):
            env.pop(key, None)
        proc = subprocess.Popen(args, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    fields = Path(f"/proc/{proc.pid}/stat").read_text().rsplit(")", 1)[1].split()
    (STATE / (name + ".json")).write_text(json.dumps({'pid': proc.pid, 'start': fields[19]}))

def health():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2) as r:
            return r.status == 200
    except Exception:
        return False

def urls():
    path = STATE / 'pinggy.log'
    return sorted(set(re.findall(r'https://[a-zA-Z0-9.-]+(?:\.free\.pinggy\.net|\.run\.pinggy-free\.link)', path.read_text(errors='replace')))) if path.exists() else []

def check():
    print('Streamlit:', 'running' if alive('streamlit') else 'stopped', '| health:', health())
    print('Pinggy:', 'running' if alive('pinggy') else 'stopped')
    if alive('pinggy'):
        for url in urls():
            print(url)
    print('Logs:', STATE)

def stop(name):
    pid = alive(name)
    if pid:
        os.killpg(pid, signal.SIGTERM)
        for _ in range(20):
            if not alive(name):
                break
            time.sleep(.1)
        if alive(name):
            os.killpg(pid, signal.SIGKILL)
    (STATE / (name + '.json')).unlink(missing_ok=True)

def start_tunnel(refresh=False):
    if not health():
        raise SystemExit('Start Streamlit on port 8501 before launching its public tunnel.')
    if refresh:
        stop('pinggy')
    launch('pinggy', ['ssh', '-T', '-p', '443', '-o', 'StrictHostKeyChecking=accept-new',
                     '-o', 'ExitOnForwardFailure=yes',
                     '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
                     '-R0:127.0.0.1:8501', 'free.pinggy.io', 'a:X-Pinggy-No-Screen:true'])
    for _ in range(30):
        if urls():
            break
        if not alive('pinggy'):
            raise SystemExit('Pinggy exited; inspect .preview/pinggy.log')
        time.sleep(1)
    check()
    if not urls():
        raise SystemExit('No tunnel URL yet; inspect .preview/pinggy.log')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'check', 'stop', 'tunnel-start', 'tunnel-refresh', 'tunnel-stop'])
    action = parser.parse_args().action
    if action == 'start':
        if not alive('streamlit') and health():
            raise SystemExit('Port 8501 already serves another app; stop that app before starting this preview.')
        launch('streamlit', [str(ROOT / '.venv/bin/python'), '-m', 'streamlit', 'run', 'app.py',
                           '--server.address', '127.0.0.1', '--server.port', '8501',
                           '--server.headless', 'true', '--browser.gatherUsageStats', 'false'])
        for _ in range(30):
            if health():
                break
            if not alive('streamlit'):
                raise SystemExit('Streamlit exited; inspect .preview/streamlit.log')
            time.sleep(1)
        if not health():
            raise SystemExit('Streamlit health check failed; inspect .preview/streamlit.log')
        start_tunnel()
    elif action == 'stop':
        stop('pinggy')
        stop('streamlit')
        check()
    elif action == 'tunnel-start':
        start_tunnel()
    elif action == 'tunnel-refresh':
        start_tunnel(refresh=True)
    elif action == 'tunnel-stop':
        stop('pinggy')
        check()
    else:
        check()
