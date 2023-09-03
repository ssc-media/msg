#! /bin/bash

set -e

# `whisper` was installed by `pip3 install -U`.
PATH="$PATH:~/.local/bin"

cd -P $(dirname $0)
cd ../..
d=$(date -d 'next Sunday - 7 days' +%Y%m%d)

if test ! -d $d; then
	git clone -q bare $d
	ln -sf $d/script ./
fi

cd $d

make step0 step1 step2 step3 step4 step5
