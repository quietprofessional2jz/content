#!/usr/bin/env bash
set -e

ssh-keyscan github.com >> ~/.ssh/known_hosts 2>&1

if [[ ! -d "content-test-data" ]]; then
    git clone git@github.com:demisto/content-test-data.git -q
fi
