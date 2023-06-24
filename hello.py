from flask import Flask
import subprocess
app = Flask(__name__)

@app.route('/')
def hello_world():
    text = """
    Đoạn trường tân thanh, thường được biết đến với cái tên đơn giản là Truyện Kiều, là một truyện thơ của đại thi hào Nguyễn Du. 
    Đây được xem là truyện thơ nổi tiếng nhất và xét vào hàng kinh điển trong văn học Việt Nam.
    Câu chuyện dựa theo tiểu thuyết Kim Vân Kiều truyện của Thanh Tâm Tài Nhân, một thi sĩ thời nhà Minh, Trung Quốc.
    Tác phẩm kể lại cuộc đời, những thử thách và đau khổ của Thúy Kiều, một phụ nữ trẻ xinh đẹp và tài năng, phải hy sinh thân mình để cứu gia đình. 
    Để cứu cha và em trai khỏi tù, cô bán mình kết hôn với một người ssđàn ông trung niên, không biết rằng anh ta là một kẻ buôn người, và bị ép làm kĩ nữ trong lầu xanh.
    """
    command_tts = f'python3 -m vietTTS.synthesizer --lexicon-file assets/infore/lexicon.txt --text="(text)" --output=clip.wav --silence-duration 0.2'

    try:
        result_tts = subprocess.check_output(
            [command_tts], shell=True)
    except subprocess.CalledProcessError as e:
        return "An error occurred while trying to fetch task status updates."

    return 'tts %s' % (result_tts)
