import sys
import glob
import time
import telegram

class check_server():

    def __init__(self):
        print('Timer Started')
        # 텔레그램봇
        my_token = '692301814:AAEfmddhyZPcO0Uzh8r5ZehfooTPOvKOOqc'
        self.mybot = telegram.Bot(token=my_token)
        self.chat_id = 544924927
        self.mybot.sendMessage(self.chat_id, text='check_logger 시작합니다.')

        delay = 80 #초 마다 확인
        self.str1 = ''
        self.str2 = ''
        self.gubun = 1
        self.count_stop = 0
        self.timer(delay)

    def timer(self,delay):

        while 1:

            aa = glob.glob(sys.path[0] + '\\log\\*') #로그파일목록 리스트화
            bb = aa[len(aa)-1] #가장 끝 파일

            f = open(bb,'r')
            cc = f.readlines()
            f.close()
            try:
                dd = cc[len(cc) - 1]  # 가장 끝 줄
                ee = dd[50:58]  # 시간

                if self.gubun == 1:
                    self.str1 = ee
                    self.gubun = 0
                else:
                    self.str2 = ee
                    self.gubun = 1

                if self.str1 == self.str2:
                    print('정지되었습니다.')
                    self.count_stop += 1
                    if self.count_stop >= 2:
                        self.mybot.sendMessage(self.chat_id, text='서버 연결을 확인하십시오!')

                    if self.count_stop == 5:
                        self.mybot.sendMessage(self.chat_id, text='check_logger 종료합니다.')
                        break
                else:
                    print('작동중입니다.')
                    self.count_stop = 0
            except:
                print('로그파일이 비어있습니다.')

            time.sleep(delay)


if __name__ == '__main__':
    t = check_server()

