include files.mak

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

step2: ch01-ebur128.txt ch01-ebu128-seek.rc ch01cut.wav maincut.wav maincut.m4a step2.rsync
	echo step2_done=1 >> files.mak

ch01-ebur128.txt: ch01.wav
	ffmpeg -i ch01.wav -filter_complex 'ebur128=metadata=1,ametadata=print:file=$@.t' -f null /dev/null
	mv $@.t $@

ch01-ebu128-seek.rc: script/ebur128_to_seek.py ch01-ebur128.txt
	script/ebur128_to_seek.py ch01-ebur128.txt >$@.t
	mv $@.t $@

ch01cut.wav: ch01.wav ch01-ebu128-seek.rc
	. ./ch01-ebu128-seek.rc ; \
	ffmpeg -ss $${seek_start} -to $${seek_end} -i ch01.wav -c copy -y .$@
	mv .$@ $@

maincut.wav: main.wav ch01-ebu128-seek.rc
	. ./ch01-ebu128-seek.rc ; \
	ffmpeg -ss $${seek_start} -to $${seek_end} -i main.wav -c copy -y .$@
	mv .$@ $@

maincut.m4a: maincut.wav
	ffmpeg -i maincut.wav -b 320k -y .$@
	mv .$@ $@

step2.rsync: maincut.m4a
	. ~/.config/msg.rc ; \
	rsync -a maincut.m4a $${web_rsync}/main-${date}-cut_around_msg.m4a ;\
	./script/dd-msg2.sh $${web_prefix}/main-${date}-cut_around_msg.m4a ${date}
	touch step2.rsync

step3: ch01cut-whisper.json
	echo step3_done=1 >> files.mak

$(step3_done)ch01cut-whisper.json: ch01cut.wav
	whisper --model medium --language ja ch01cut.wav --output_format json
	mv ch01cut.json ch01cut-whisper.json
