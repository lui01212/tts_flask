from flask import Flask
import subprocess
from subprocess import Popen, PIPE
from subprocess import check_output

def get_shell_script_output_using_communicate():
    session = Popen(['./some.sh'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = session.communicate()
    if stderr:
        raise Exception("Error "+str(stderr))
    return stdout.decode('utf-8')

def get_shell_script_output_using_check_output():
    stdout = check_output(['quick_start.sh']).decode('utf-8')
    return stdout

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<pre>'+get_shell_script_output_using_check_output()+'</pre>'
