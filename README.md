# Eos contracts compilation service

## Requirements:

- python3
- pipenv
- docker

## Installation

```
cd compiler
docker build -t eos_compiler .

cd ../bin
pipenv install
echo DOCKER_HOST=\'\' > .env
echo SERVICE_PORT=5001 >> .env
```

## Running

```
cd bin
pipenv run python3 wsgi_app.py
```


## Compiler's dockerfile

Based on https://github.com/mixbytes/eos-compile-service/

compiler/Dockerfile <- repo/docker/Dockerfile
compiler/nodeosd.sh <- repo/docker/nodeosd.sh