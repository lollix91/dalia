import os 
import git
import time
import json
import logging
import asyncio
import argparse
import threading
import subprocess
logging.basicConfig(level=logging.INFO)

def port_busy(port):
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    logging.info(result.stdout)
    return f"{port}" in result.stdout

def check_sicstus(root):
    sicstus = ""
    path    = os.path.join(root, 'files', 'sicstus', 'bin', 'sicstus')
    if os.path.isfile(path) and os.access(path, os.X_OK):
        sicstus = path
    return sicstus

def load_src(root):
    result      = {
        "agents": dict(),
        "comm": ""
    }
    mappingpath = os.path.join(root, 'src', 'mapping.json')
    try:
        with open(mappingpath, 'r') as f:
            mapping = json.loads(f.read())
    except Exception as e:
        logging.exception(f"{mappingpath} does not exist")
        return {} 
    try:
        for name, type in mapping.items():
            path = os.path.join(root, 'src', 'types', f'{type}.txt') 
            assert os.path.isfile(path)
            with open(path, 'r') as f:
                code = f.read().strip()
            result["agents"][name] = {
                "type": type,
                "code": code
            }
    except Exception as e:
        logging.exception(f"problem with mappings in {mappingpath}")
        return {} 
    commpath = os.path.join(root, 'src', 'conf', f'communication.con')
    try:
        assert os.path.isfile(commpath)
        with open(commpath, 'r') as f:
            code = f.read().strip()
            result["comm"] = code
    except Exception as e:
        logging.exception(f"problem with file {commpath}")
        return {} 
    return result

def rmdir(path):
    if os.path.exists(path) and os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(path)

def shell(cmd):
    p = subprocess.Popen(cmd, shell=True)
    p.wait()


def build(*, root, sicstuspath, dalipath):
    src = load_src(root)
    if not src:
        return
    
    cmd = "pkill -9 sicstus 2>/dev/null || true"
    shell(cmd)
    dalipath = os.path.join(dalipath, 'src')
    sicstus  = os.path.join(sicstuspath, 'bin', 'sicstus')
    wrk = os.path.join(root, 'wrk')
    rmdir(wrk)
    agentsdir = os.path.join(wrk, 'agents')
    setupsdir = os.path.join(wrk, 'setups')
    confdir  = os.path.join(wrk, 'conf')
    os.makedirs(setupsdir, exist_ok=True)
    os.makedirs(agentsdir, exist_ok=True)
    os.makedirs(confdir, exist_ok=True)
    with open(os.path.join(confdir, f'communication.con'), 'w') as f:
        f.write(src["comm"])
    port = 3010
    logging.info(f"waiting for port {port} to be free")
    while port_busy(port):
        time.sleep(1)
    time.sleep(5)
    cmd = f"{sicstus} --noinfo -l {os.path.join(dalipath, 'active_server_wi.pl')} --goal go."
    logging.info(cmd)
    threading.Thread(target=shell, args=(cmd,), daemon=True).start()
    time.sleep(5)
    for name in src["agents"]:
        with open(os.path.join(agentsdir, f'{name}.txt'), 'w') as f:
            f.write(src['agents'][name]["code"])
        os.chmod(os.path.join(agentsdir, f'{name}.txt'), 0o755)
        setup = f"agent('{agentsdir}/{name}', '{name}','no',italian,['{confdir}/communication'],['{dalipath}/communication_fipa','{dalipath}/learning','{dalipath}/planasp'],'no','{dalipath}/onto/dali_onto.txt',[])."
        with open(os.path.join(setupsdir, f'{name}.txt'), 'w') as f:
            f.write(setup)
        os.chmod(os.path.join(setupsdir, f'{name}.txt'), 0o755)
        cmd = " ".join([sicstus, '--noinfo', '-l', os.path.join(dalipath, 'active_dali_wi.pl'), '--goal', f'"start0(\'{os.path.join(setupsdir, f'{name}.txt')}\')."'])
        logging.info(f"cmd: {cmd}")
        threading.Thread(target=shell, args=(cmd,), daemon=True).start()
        time.sleep(5)
    cmd=f"{sicstus} --noinfo -l {os.path.join(dalipath, 'active_user_wi.pl')} --goal user_interface."
    shell(cmd)


    
if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--dalipath', type=str, required=True)
    argparser.add_argument('--sicstuspath', type=str, required=True)
    args = argparser.parse_args()
    root = os.path.dirname(os.path.abspath(__file__))
    build(root=root, sicstuspath=os.path.abspath(args.sicstuspath), dalipath=os.path.abspath(args.dalipath))