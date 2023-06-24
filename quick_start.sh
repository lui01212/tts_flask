echo "Generate audio clip"
text=`cat transcript.txt`
cd /home/buivanluyn/content2/vietTTS/
python3 -m vietTTS.synthesizer --text "$text" --output assets/infore/clip.wav --lexicon-file assets/infore/lexicon.txt --silence-duration 0.2