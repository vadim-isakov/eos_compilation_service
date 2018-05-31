#!/usr/bin/env python3
import random
import sys
import os
import json
import tempfile
import subprocess

import time
from flask import Flask, request


DOCKER_HOST = os.environ.get("DOCKER_HOST", '127.0.0.1:2375')

LIMITS = [
    '--memory=128m',
    '--memory-swap=128m',
    '--ulimit', 'core=0',
    '--ulimit', 'data=134217728',
    '--ulimit', 'rss=134217728',
    '--ulimit', 'locks=134217728',
    '--ulimit', 'fsize=16777216',
    '--ulimit', 'nofile=256',
    # '--ulimit', 'cpu=3', # only 3 works
    '--ulimit', 'nproc=16',
    '--net', 'none',
]



app = Flask(__name__)


@app.route('/compile', methods=['POST'])
def compile():
    args = _get_input()

    if 'source' not in args or type(args['source']) != str:
        return _send_error("Invalid parameters for compiler call/1")

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chmod(tmpdir, 0o755)

        file = open(os.path.join(tmpdir, 'contract.cpp'), "w")
        file.write(args["source"])
        file.close()

        bin, err = run(tmpdir, 'outname')
        if err:
            return _send_error("Compilation error/1")

        abi, err = run(tmpdir, 'genabi')
        if err:
            return _send_error("Compilation error/2")


        return json.dumps(
            {
                'result': 'success',
                'bin': bin.decode('utf-8'),
                'abi': abi.decode('utf-8')
            }
        )


def l(v):
    print(repr(v), file=sys.stderr)
    return v


def _get_input():
    print('[DEBUG]: got input: {}'.format(request.data))
    return json.loads(request.data.decode('utf-8'))


def _send_error(string):
    print('[ERROR]: {}'.format(string))
    return _send_output({
        'result': 'error',
        'error_descr': string
    })


def _send_output(output):
    return json.dumps(output)


def run(tmpdir, flag):
    command = ['docker']
    command += ["--host", DOCKER_HOST] if DOCKER_HOST else []

    pr = subprocess.Popen(
        command
        + [
            "run", "--rm",
            "-v", "{}:/input/".format(tmpdir),
            '--name', 'compiler_container_{}_{}'.format(str(round(time.time() * 1000000)), random.randint(0, 10 ** 9))
        ]
        + LIMITS
        + ["eos_compiler"]
        + [
            '/usr/bin/timeout', '-s', 'KILL', '5',
            'sudo', '-u', 'nobody',
            '/bin/bash', '-c', '/opt/eosio/bin/eosiocpp --{} /tmp/contract.out /input/contract.cpp &> /dev/null; cat /tmp/contract.out'.format(flag)
        ],
        stdout=subprocess.PIPE
    )
    out, err = pr.communicate()

    if pr.returncode > 0:
        return None, _send_error("Error while run compiler/1")

    return out, None


if __name__ == '__main__':
    app.run(host="0.0.0.0")
