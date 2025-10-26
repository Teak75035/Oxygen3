import os
import subprocess

def run_scripts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts = ['hower.py', 'oxyver3.py']
    processes = []
    for script in scripts:
        script_path = os.path.join(base_dir, script)
        if os.path.exists(script_path):
            p = subprocess.Popen(['python', script_path])
            processes.append(p)
        else:
            print(f"Script not found: {script_path}")
    for p in processes:
        p.wait()

if __name__ == "__main__":
    run_scripts()