#! /bin/bash
wget https://github.com/yyuu/pyenv/archive/v1.0.10.tar.gz
tar -xaf v1.0.10.tar.gz
export PATH=./pyenv-1.0.10/bin:$PATH
export PYENV_ROOT=$HOME/pyenv
mkdir -p "$HOME/pyenv"
eval "$(pyenv init -)"
pyenv install 3.5.3
pyenv local system 3.6.1 3.5.3