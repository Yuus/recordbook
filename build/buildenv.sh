#!/bin/sh
echo Creating environment
virtualenv --no-site-packages .env

echo Install PIP inside virtual environment
./.env/bin/easy_install pip

echo Installing dependencies
./.env/bin/pip install -E .env -r ./build/pipreq.txt

