import os 
import git
import glob
import json
import logging
import asyncio
import subprocess

def check_port(port):
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    logging.info(result.stdout)
    return f"{port}" not in result.stdout

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

def build(root):
    src = load_src(root)
    if not src:
        return
    dalipath = os.path.join(root, 'files', 'dali', 'src')
    sicstus  = os.path.join(root, 'files', 'sicstus', 'bin', 'sicstus')
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
    procs = []
    for name in src["agents"]:
        with open(os.path.join(agentsdir, f'{name}.txt'), 'w') as f:
            f.write(src['agents'][name]["code"])
        os.chmod(os.path.join(agentsdir, f'{name}.txt'), 0o755)
        setup = f"agent('{agentsdir}/{name}', '{name}','no',italian,['{confdir}/communication'],['{dalipath}/communication_fipa','{dalipath}/learning','{dalipath}/planasp'],'no','{dalipath}/onto/dali_onto.txt',[])."
        with open(os.path.join(setupsdir, f'{name}.txt'), 'w') as f:
            f.write(setup)
        os.chmod(os.path.join(setupsdir, f'{name}.txt'), 0o755)
        procs +=[
            subprocess.Popen([sicstus, '--noinfo', '-l', os.path.join(dalipath, 'active_dali_wi.pl'), '--goal', f"\"start0('{os.path.join(setupsdir, f'{name}.txt')}').\""])
        ]
        
    for p in procs:
        p.wait()
    

root = os.path.dirname(os.path.abspath(__file__))
build(root)