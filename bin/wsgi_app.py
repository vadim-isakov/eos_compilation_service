#!/usr/bin/env python3
import random
import sys
import os
import json
import tempfile
import subprocess

import time
from flask import Flask, abort, request


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
    '--ulimit', 'cpu=1',
    '--ulimit', 'nproc=16',
    '--net', 'none',
]



app = Flask(__name__)


@app.route('/compile', methods=['POST'])
def construct():
    args = _get_input()

    if 'source' not in args or type(args['source']) != str:
        return _send_error("Invalid parameters for compiler call/1")


    with tempfile.TemporaryDirectory() as tmpdir:
        os.chmod(tmpdir, 0o755)

        file = open(os.path.join(tmpdir, 'contract.cpp'),"w")
        file.write(args["source"])
        file.close()

        command = ['docker']
        command += ["--host", DOCKER_HOST] if DOCKER_HOST else []

        pr = subprocess.Popen(
            command
            + [
                "run", "-i", "--rm",
                "-v", "{}:/code:ro".format(tmpdir),
                '--name', 'compiler_container_{}_{}'.format(str(round(time.time()*1000000)), random.randint(0, 10**9))
            ]
            + LIMITS
            + ["eos_compiler"],
            stdin =subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        output = pr.communicate()

        if pr.returncode > 0:
            return _send_error("Error while run compiler/1")

        try:
            response_json = json.loads(output[0].decode('utf-8'))
        except Exception as e:
            print('[DEBUG] {}'.format(str(e)))
            print('[DEBUG] {}'.format(str(output)))
            return _send_error("Error while parsing response from compiler/1")

        if 'bin' not in response_json or 'abi' not in response_json \
                or type(response_json['bin']) != str or type(response_json['abi']) != str:
            return _send_error("Error while parsing response from compiler/2")

        return output[0]


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



if __name__ == '__main__':
    app.run(host="0.0.0.0")
