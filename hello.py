from flask import Flask
from flask import send_file
from underthesea import sent_tokenize
from pydub import AudioSegment

import subprocess
app = Flask(__name__)

@app.route('/')
def hello_world():
    command_tts = ""
    cattexxt = ""
    step = ""
    text_cut = ""
    text = """
        Diệp Phàm và Bàng Bác lực áp Hàn Phi Vũ, làm cho mọi người chấn kinh trợn mắt há mồm, 2 thiếu niên chỉ có 11, 12 tuổi này khiến cho mọi người trở nên hồ đồ, rõ ràng là chưa tu luyện được Thần Lực Nguyên Tuyền, vậy mà lại đánh cho cháu của 1 vị trưởng lão ngất đi, suýt nữa thì bị phế, chính điều này đã làm cho mọi người cứng họng, chẳng biết nói gì nữa.
    
        Hai người này quá mạnh mẽ!
        
        Nhưng mà mới chỉ 11, 12 tuổi, chẳng lẽ họ có Thần Lực?
        
        Tay không đối địch, lực áp Hàn Phi Vũ, lại đánh bay Thanh Mộc ấn mà Hàn trưởng lão ban xuống, người này thật không còn gì để nói nữa.
        
        Mọi người bàn tán rất sôi nổi.
        
        Lúc này ngay cả những ở dưới vách núi nhập môn sớm hơn, những đệ tử có tu vi cao thâm, cũng đều chú ý tới chuyện vừa xảy ra, sau khi biết cháu của Hàn trưởng lão là Hàn Phi Vũ bị hành hung, cũng nghị luận không ngớt.
        
        Hai thiếu niên này nhìn bề ngoài thì thanh thú, nhưng lại bạo lực đến vậy, thật đúng là nhìn người không thể nhìn tướng mạo...
        
        Diệp Phàm và Bàng Bác cũng biết được tình hình, biết mình đã trở thành tiêu điểm chú ý của mọi người, những đệ tử khác ở dưới vách núi sau khi được nghe kể lại tình huống, cũng chạy tới nơi này, muốn gặp mặt 2 người mạnh mẽ này.
        
        Cái gì, tên Bàng Bác kia là Mầm Tiên?
        
        Khi mọi người biết được tin này, tất cả những đệ tự nhập môn sớm hơn đều giật mình, họ biết Mầm Tiên có ý nghĩa như thế nào, đó chính là người được kế thừa và là niềm hy vọng của Linh Khư Động Thiên, là người có khả năng thống lĩnh môn phải, trở thành một nhân vật phong vân huy hoàng.
        
        Hóa ra là Mầm Tiên, khó trách lại thần dũng như vậy, đúng là người mang dị bẩm.
        
        Hàn Phi Vũ lần này đá vào tấm sắt rồi, sau này hắn cũng không được trả thù, chỉ có thể nuốt cục tức này xuống mà thôi...
        
        Bây giờ, ánh mắt của mọi người nhìn về phía Bàng Bác rất phức tạp, trong lòng mỗi người đều có tư vị không thể nói thành lời, có không ít người nhanh chóng quyết định, sau này phải cùng Bàng Bác quan hệ thật tốt.
        
        Lúc này, Diệp Phàm và Bàng Bác không rảnh rỗi gì cả, cũng không để ý tới ánh mắt của mọi người, nhặt từng bình nhỏ ở trên mặt đất lên, tổng cộng có hơn 30 bình Bách Thảo dịch.
        
        Mấy thiếu niên tới gây hấn đều bị Diệp Phàm và Bàng Bác cắm ngược đầu xuống bùn, nhưng Bách Thảo dịch mà chúng cướp của người khác thì đều bị 2 người giữ lại.
        
        Để tử mới nhập môn phải 3 tháng mới có thể nhận được 1 lần Bách Thảo dịch, vì vậy nó vô cùng quý giá, những người xung quanh thấy lúc này 2 người có tới tận ba mươi mấy bình, nhất thời đỏ hết cả mắt lên.
        
        Mấy tên gia hỏa kia… đã tu thành thần văn...Chắc chắn trên người chúng còn nhiều thứ tốt hơn nữa
        
        Diệp Phàm và Bàng Bác vẫn còn chưa thấy thỏa mãn, đưa mắt nhìn mấy thanh niên bị cắm ngược trong bùn, mấy người kia đã tu luyện được một chút Thần Lực, lại còn bồi dưỡng ra được cả Thần văn, tu vi cao hơn đệ tử phổ thông bình thường, thì chắc chắn còn là những thiếu niên giàu có.
        
        Hai người liếc mắt nhìn nhau, rẽ nước đắp đập, trước tiên đem 5 người kéo ra khỏi vũng bùn, sau đó bắt đầu khám xét. Bạn đang đọc truyện được lấy tại chấm cơm.
        
        Sao trên mỗi người chỉ có mấy bình Bách Thảo dịch...
        
        Diệp Phàm và Bàng Bác tìm kỹ trên thân thể bọn họ, chỉ thấy mỗi thì phát hiện mỗi người chỉ có 5 bình Bách Thảo dịch, còn tưởng có nhiều tài bảo lắm, ánh mắt 2 người tỏ vẻ tiếc nuối, nhất thời làm cho những người đứng xem không biết nói gì cho phải.
        
        Hôm nay, mấy ngọn Sơn nhai đều phân phát Bách Thảo dịch, căn cứ theo tu vi cao thấp khác nhau, mà có số lượng Bách Thảo dịch khác nhau, mấy thanh niên này mỗi người được nhân 5 bình là không tồi rồi.
    """
    try:
        text_cut = sent_tokenize(text) 
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

    return 'tts %s cat %s' % (result_tts, result_cat)


@app.route('/download')
def downloadFile ():
    #For windows you need to use drive name [ex: F:/Example.pdf]
    path = "./clip.wav"
    return send_file(path, as_attachment=True)
