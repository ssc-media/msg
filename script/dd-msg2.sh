#! /bin/bash

date_text="$(date -d "$2" +'%m月%d日')"
. ~/.config/msg.rc

~/script/dd.py --channel $dd_channel --send-text "${date_text}の礼拝 (メッセージ前後) の録音です。 $1"
