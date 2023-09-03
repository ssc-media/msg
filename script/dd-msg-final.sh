#! /bin/bash

url_data="$1"
date_text="$(date -d "$2" +'%m月%d日')"
dialog_log="$3"
url_preview="$(sed 's;/data/audio/;/audio/;' <<<"$1")"
. ~/.config/msg.rc

~/script/dd.py --channel $dd_channel --send-text - <<-EOF
${dd_mention}
${date_text}の礼拝メッセージの録音です。
$url_data (ダウンロード用)
$url_preview (プレビュー用)
EOF

{
echo 'カット箇所の情報:'
echo '```'
grep -B5 -A5 ^cut "$dialog_log" | awk -v FS='\t' '{print $NF}'
echo '```'
} |
~/script/dd.py --channel $dd_channel --send-text -
