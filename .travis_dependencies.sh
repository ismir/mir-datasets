#!/bin/sh

ENV_NAME="test-environment"
set -e

conda_create ()
{

    hash -r
    conda config --set always_yes yes --set changeps1 no
    conda update -q conda
    conda config --add channels pypi
    conda info -a
    deps='pip pytest'

    conda create -q -n $ENV_NAME "python=$TRAVIS_PYTHON_VERSION" $deps
    conda update --all
}

src="$HOME/env/miniconda$TRAVIS_PYTHON_VERSION"
if [ ! -d "$src" ]; then
    mkdir -p $HOME/env
    pushd $HOME/env

        # Download miniconda packages
        wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh -O miniconda.sh;

        # Install both environments
        bash miniconda.sh -b -p $src

        export PATH="$src/bin:$PATH"
        conda_create

        activate $ENV_NAME

        deactivate
    popd
else
    echo "Using cached dependencies"
fi
