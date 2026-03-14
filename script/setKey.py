#!/usr/bin/env python3
"""
Distribute SSH keys across cluster nodes for passwordless SSH.
Run from your laptop (with SSH access to all nodes) or from the master node.

Usage:
  # Edit USER and SERVER_LIST below, then:
  python3 setKey.py

  # Or pass via environment (one host per line in file):
  USER=myuser NODES_FILE=./nodes.txt python3 setKey.py

  # Or pass nodes as comma-separated:
  USER=myuser NODES="node1,node2,node3" python3 setKey.py
"""
import os
import sys

# Defaults (edit these or override via env)
USER = os.environ.get('USER', 'xuchuan')
SERVER_LIST = [
    'clnode279.clemson.cloudlab.us',
    'clnode281.clemson.cloudlab.us',
    'clnode264.clemson.cloudlab.us',
    'clnode259.clemson.cloudlab.us',
    'clnode267.clemson.cloudlab.us',
    'clnode271.clemson.cloudlab.us',
    'clnode278.clemson.cloudlab.us',
    'clnode270.clemson.cloudlab.us',
    'clnode282.clemson.cloudlab.us',
    'clnode274.clemson.cloudlab.us',
]

# Override from env (use SETKEY_USER to avoid clashing with shell USER)
if os.environ.get('SETKEY_USER'):
    USER = os.environ['SETKEY_USER']
if os.environ.get('NODES'):
    SERVER_LIST = [s.strip() for s in os.environ['NODES'].split(',') if s.strip()]
elif os.environ.get('NODES_FILE'):
    with open(os.environ['NODES_FILE']) as f:
        SERVER_LIST = [line.strip() for line in f if line.strip()]


def main():
    print(f"User: {USER}")
    print(f"Nodes: {len(SERVER_LIST)}")
    for s in SERVER_LIST:
        print(f"  - {s}")

    # Generate keys on each node
    for s in SERVER_LIST:
        cmd = f'ssh {USER}@{s} -o StrictHostKeyChecking=no "ssh-keygen -t rsa -b 2048 -N \'\' -f ~/.ssh/id_rsa"'
        if os.system(cmd) != 0:
            print(f"Warning: keygen failed on {s}", file=sys.stderr)

    pub_key_list = []
    for s in SERVER_LIST:
        cmd = f'scp -o StrictHostKeyChecking=no {USER}@{s}:.ssh/id_rsa.pub ./'
        os.system(cmd)
        if os.path.exists('id_rsa.pub'):
            with open('id_rsa.pub') as f:
                pub_key_list.append(f.readline())

    # Collect existing authorized_keys from first node
    cmd = f'scp -o StrictHostKeyChecking=no {USER}@{SERVER_LIST[0]}:.ssh/authorized_keys ./'
    os.system(cmd)
    with open('authorized_keys', 'a') as f:
        for key in pub_key_list:
            f.write(key)

    # Distribute to all nodes
    for s in SERVER_LIST:
        cmd = f'scp -o StrictHostKeyChecking=no ./authorized_keys {USER}@{s}:.ssh/authorized_keys'
        os.system(cmd)

    print("Done. Verify with: ssh <node> hostname")


if __name__ == '__main__':
    main()
