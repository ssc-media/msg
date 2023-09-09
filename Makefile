include files.mak

.SUFFIXES: .txt .wav .flac
.PRECIOUS: %-ebur128.txt

%-ebur128.txt: %.wav
	ffmpeg -i $< -filter_complex 'ebur128=metadata=1,ametadata=print:file=$@.t' -f null /dev/null
	mv $@.t $@

%-ebur128.txt: %.flac
	ffmpeg -i $< -filter_complex 'ebur128=metadata=1,ametadata=print:file=$@.t' -f null /dev/null
	mv $@.t $@

# Step 0: Prepare files

step0: ${reac_file}
	echo step0_done=1 >> files.mak

$(step0_done)files.mak: ./script/step0.sh
	./script/step0.sh > $@.t
	mv $@.t $@

$(step0_done)${reac_file}: ${reac_file_abs}
	ln -s ${reac_file_abs}

step1: ch01.wav main.wav
	echo step1_done=1 >> files.mak

$(step1_done)ch01.wav $(step1_done)main.wav: ${reac_file}
	~/script/reac2wav.sh --only-channel 9,7,8 ${reac_file}

step2: ch01-ebur128.txt ch01-ebu128-seek.rc ch01cut.flac maincut.flac maincut.m4a step2.rsync
	echo step2_done=1 >> files.mak

ch01-ebu128-seek.rc: script/ebur128_to_seek.py ch01-ebur128.txt
	script/ebur128_to_seek.py --time-candidate-center 2700 ch01-ebur128.txt >$@.t
	mv $@.t $@

$(step2_done)ch01cut.flac: ch01.wav ch01-ebu128-seek.rc
	. ./ch01-ebu128-seek.rc ; \
	ffmpeg -ss $${seek_start} -to $${seek_end} -i ch01.wav -y .$@
	mv .$@ $@

$(step2_done)maincut.flac: main.wav ch01-ebu128-seek.rc
	. ./ch01-ebu128-seek.rc ; \
	ffmpeg -ss $${seek_start} -to $${seek_end} -i main.wav -y .$@
	mv .$@ $@

maincut.m4a: maincut.flac
	ffmpeg -i maincut.flac -b:a 320k -y .$@
	mv .$@ $@

step2.rsync: maincut.m4a
	. ~/.config/msg.rc ; \
	rsync -a maincut.m4a $${web_rsync}/main-${date}-cut_around_msg.m4a ;\
	./script/dd-msg2.sh $${web_prefix}/main-${date}-cut_around_msg.m4a ${date}
	touch step2.rsync

step3: ch01cut-whisper.json
	echo step3_done=1 >> files.mak

$(step3_done)ch01cut-whisper.json: ch01cut.flac
	whisper --model large --language ja ch01cut.flac --output_format json
	mv ch01cut.json ch01cut-whisper.json

step4: ch01cut-seek.rc
	echo step4_done=1 >> files.mak

$(step4_done)ch01cut-seek.rc: ch01cut-whisper.json
	script/whisper2cutmsg.py -be --dialog-log ch01cut-seek.rc.log ch01cut-whisper.json >.$@
	mv .$@ $@

step5: msg-${date}.mp3 step5.rsync step5.dd
	echo step5_done=1 >> files.mak

maincut-loudness-seek.rc: ch01cut-seek.rc maincut-ebur128.txt
	. ./ch01cut-seek.rc ; \
	script/ebur128_to_seek.py \
		--time-range-start=$${seek_start} --time-range-end=$${seek_end} \
		--time-add-start=-1.5 \
		--time-add-end=3 \
		--time-fade=0.7 \
	maincut-ebur128.txt > .$@
	mv .$@ $@

maincut-whisper-loudness-normalize.flac: maincut.flac maincut-loudness-seek.rc
	. ./maincut-loudness-seek.rc ; \
	ffmpeg \
		-loglevel info \
		-ss $${seek_start} -to $${seek_end} -i maincut.flac \
		-filter_complex "loudnorm=i=-21.0:print_format=summary" \
		-f null -y /dev/null 2> $@.loudnorm.txt ; \
	ffmpeg \
		-ss $${seek_start} -to $${seek_end} -i maincut.flac \
		-filter_complex "loudnorm=i=-21.0:$$(./script/loudnorm2opt.awk $@.loudnorm.txt):print_format=summary,afade=t=in:d=0.5,afade=t=out:d=0.5:start_time=$${fade_out_start}" \
		-ar 48000 \
		-y .$@
	mv .$@ $@

msg-${date}.mp3: maincut-whisper-loudness-normalize.flac
	ffmpeg -i $< .$@
	mv .$@ $@

step5.rsync: msg-${date}.mp3
	. ~/.config/msg.rc ; \
	rsync -a msg-${date}.mp3 $${web_rsync}
	touch $@

step5.dd: step5.rsync
	. ~/.config/msg.rc ; \
	./script/dd-msg-final.sh $${web_prefix}msg-${date}.mp3 ${date} ch01cut-seek.rc.log
	touch $@
