from pywinauto import application
from pywinauto import timings
import time
import os

app = application.Application()
app.start("C:/KiwoomFlash3/bin/nkministarter.exe")

title = "번개3 Login"
dlg  = timings.WaitUntilPasses(20, 0.5, lambda: app.window_(title=title))

pass_ctrl = dlg.Edit2
pass_ctrl.SetFocus()
pass_ctrl.TypeKeys('thwjd2')
#로그인 비밀번호

cert_ctrl = dlg.Edit3
cert_ctrl.SetFocus()
cert_ctrl.TypeKeys('thwjddl2@2')
#공인인증서 비밀번호

btn_ctrl = dlg.Button0
btn_ctrl.Click()

time.sleep(60)
os.system("taskkill /im nkmini.exe")
#업데이트 후 종료