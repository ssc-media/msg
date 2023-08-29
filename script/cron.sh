#! /bin/bash

set -e

cd -P $(dirname $0)
cd ../..
d=$(date -d 'this Sunday' +%Y%m%d)

if test ! -d $d; then
	git clone -q bare $d
	ln -sf $d/script ./
fi

make step0 step1 step2 step3
