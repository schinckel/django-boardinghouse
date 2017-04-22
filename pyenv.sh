#! /bin/bash
export PYENV_ROOT="${HOME}/pyenv"
mkdir -p "${PYENV_ROOT}"
wget https://github.com/yyuu/pyenv/archive/v1.0.10.tar.gz
tar -xaf v1.0.10.tar.gz --strip-components=1 --directory="${PYENV_ROOT}"
export PATH="${PYENV_ROOT}/bin:${PATH}"
export PYENV_ROOT

eval "$(pyenv init -)"
pyenv install --skip-existing 3.6.1
pyenv install --skip-existing 3.5.3
pyenv global system 3.6.1 3.5.3

python --version
pyenv version