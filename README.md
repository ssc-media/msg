# Sermon cut script for Sakae Shalom Church

This repository is a script set to cut the sermon part.

## Inputs

- REAC packet capture file.
  Expecting these channel assign
  - 9: Microphone from pastor
  - 7, 8: Stereo-linked channel that goes to the streaming
  Expected file path is `~/reac/reac-%Y%m%d-%H%M%S.pcap`

## Outputs

- MP3 file that has only the sermon part.
- Informative data for debugging.
- Also send some of these info to Discord channel.

## Steps

- Step 0
  This step collects setup information such as REAC file path.
- Step 1
  This step converts REAC capture file to wave files.
- Step 2
  This step cut the audio into the part including the sermon and before/after the sermon using loudness of the file.
- Step 3
  This step recognizes the sermon. This is the most time consuming part.
- Step 4
  This step determines the cut point roughly within several seconds based on the text from the previous step.
  Note: If the result is incorrect, manual adjustment is required.
  At first, check the log file `ch01cut-seek.rc.log` has correct `cut-begin` and `cut-end` flags.
  If not, use one of these strategy to fix it.
  - Edit `script/whisper2cutmsg.py` so that the results become correct.
  - Manually edit `ch01cut-seek.rc` to point the desired time to cut.
- Step 5
  This step finalizes the output file by doing these things and send the result to Discord channel.
  - Accurately cut based on the short-term loudness.
  - Fade-in and fade-out at the beginning and the end, respectively.
  - Normalize the loudness.

## Link
- https://sakaeshalom.podbean.com/
