from flask import Flask, request
from flask import send_file
from underthesea import sent_tokenize
from underthesea import text_normalize
from pydub import AudioSegment
from vietnam_number import n2w
from pyvi import ViTokenizer

import re

import subprocess
app = Flask(__name__)


def process_text(text):
    # Phân tách từ trong văn bản tiếng Việt
    tokens = ViTokenizer.tokenize(text)

    # Xử lý các từ chứa "z", "j", "w" và "F" dựa trên ngữ cảnh
    processed_tokens = []
    for token in tokens.split():
        if any(char in token for char in ['z', 'j', 'w', 'F']):
            # Có ít nhất một chữ cái cần xử lý trong từ
            # Tiến hành xử lý từ
            token = token.replace('z', 'd').replace('j', 'gi').replace('w', 'qu').replace('F', 'Ph')
        processed_tokens.append(token)

    # Gộp các từ đã xử lý thành văn bản mới
    processed_text = ' '.join(processed_tokens)

    return processed_text


def replace_numbers_with_letters(text):
    
    def replace(match):
        number = match.group(0)
        return n2w(number)
    
    return re.sub(r'\d+', replace, text)


def remove_meaningless_characters(text):
    meaningless_chars = ['-', '_', '(', ')', '[', ']', '{', '}', '<', '>', '*', '/', '\\', '|', '@', '#', '$', '%', '^', '&', '=', '+', '~', '`', '"', "'", '\n', '\r', '\t']
    
    for char in meaningless_chars:
        text = text.replace(char, '')
    
    return text

# Endpoint to create wav from text
@app.route('/create_wav_from_text', methods=["POST"])
def add_guide():
    text = request.json['text']
    command_tts = ""
    cattexxt = ""
    step = ""
    text_cut = ""
    try:
        text_cut_nomal = sent_tokenize(text)
        text_cut_nomal = list(map(remove_meaningless_characters, text_cut_nomal))
        text_cut_nomal = list(map(replace_numbers_with_letters, text_cut_nomal))
        text_cut_nomal = list(map(process_text, text_cut_nomal))
        text_cut = list(map(text_normalize, text_cut_nomal))
        for i in range(len(text_cut)):
            cattexxt = cattexxt + step +  f'clip{i}.wav'
            step = " "

        command_cat = f'cat {cattexxt} > clip.wav'

        for i in range(len(text_cut)):
            command_tts = f'python3 -m vietTTS.synthesizer --lexicon-file assets/infore/lexicon.txt --text="{text_cut[i]}" --output=clip{i}.wav --silence-duration 0.2'
            result_tts = subprocess.check_output(
                        [command_tts], shell=True)
            
        result_cat = subprocess.check_output(
                [command_cat], shell=True)

        combined_sounds = AudioSegment.from_wav(f'clip0.wav')

        for i in range(len(text_cut)):
            if i > 0 :
                sound = AudioSegment.from_wav(f'clip{i}.wav')
                combined_sounds += sound

        combined_sounds.export("clip.wav", format="wav")

    except subprocess.CalledProcessError as e:
        return "An error occurred while trying to fetch task status updates."

    return {
        "url": request.host_url + "download"
    }


@app.route('/')
def hello_world():
    return 'hello_world!'


@app.route('/download')
def downloadFile ():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "./clip.wav"
    return send_file(path, as_attachment=True)
