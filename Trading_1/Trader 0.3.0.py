import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import pandas as pd
import telegram
import requests


form_class = uic.loadUiType("trader_v3.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.tr = 0 #총TR요청횟수

        #텔레그램봇
        my_token = '692301814:AAEfmddhyZPcO0Uzh8r5ZehfooTPOvKOOqc'
        self.mybot = telegram.Bot(token=my_token)
        self.chat_id = 544924927

        self.kiwoom = Kiwoom() #키움인스턴스 생성
        self.kiwoom.comm_connect() #API로그인

        self.ts_1_p = 'False' #거래전략1 초기값

        # Timer1
        self.timer = QTimer(self)
        self.timer.start(1000) #1초 상태바
        self.timer.timeout.connect(self.timeout)

        # Timer2
        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 25) #25초 잔고조회
        self.timer2.timeout.connect(self.timeout2)

        # Timer3
        self.timer3 = QTimer(self)
        self.timer3.start(1000 * 30) #30초 매수전략1
        self.timer3.timeout.connect(self.timeout3)

        # Timer4
        self.timer4 = QTimer(self)
        self.timer4.start(1000 * 33)  # 33초 매도전략
        self.timer4.timeout.connect(self.timeout4)

        # Timer5
        self.volume_start = 'false'
        self.timer5 = QTimer(self)
        #self.timer5.start(1000 * 60)  # 60초 9시에 급등주알고리즘 시작하기
        #self.timer5.timeout.connect(self.timeout5)

        # Timer7
        self.timer7 = QTimer(self)
        self.timer7.start(1000 * 1800)  # 30분 중간보고
        self.timer7.timeout.connect(self.timeout7)

        self.list700 = []
        self.list600 = []
        self.buy_list = []

        #버튼, 이벤트발생
        self.lineEdit.textChanged.connect(self.code_changed) #종목코드 입력시
        self.pushButton.clicked.connect(self.send_order) #현금주문 버튼 클릭시
        self.pushButton_2.clicked.connect(self.check_balance) #계좌정보 조회
        self.pushButton_3.clicked.connect(self.trading_strategy_1) #거래전략1호
        self.pushButton_4.clicked.connect(self.quit_app) #앱종료
        self.pushButton_4.clicked.connect(QCoreApplication.instance().quit)  # 앱종료
        self.pushButton_5.clicked.connect(self.test_button)  # 테스트버튼

        #계좌정보
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        #프로그램시작알림
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") +"ㅣ 프로그램이 시작되었습니다.")
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "\n프로그램이 시작되었습니다.")

    def test_button(self):
        self.timeout7()

    #종료
    def quit_app(self):
        #계좌정보요청
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(1)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
        self.tr += 1
        bb = self.kiwoom.opw00018_output['single']
        myaccount = '총매입금액: %s원\n총평가금액: %s원\n총평가손익금액: %s원\n총수익률(%%): %s\n추정예탁자산: %s원' % (bb[0],bb[1],bb[2],bb[3],bb[4])



        a = len(self.kiwoom.opw00018_output['multi'])
        if a !=0:
            name = []
            num = []
            buy = []
            price = []
            earn = []
            ret = []
            for i in range(a):
                name.append(self.kiwoom.opw00018_output['multi'][i][0])
                num.append(self.kiwoom.opw00018_output['multi'][i][1])
                buy.append(self.kiwoom.opw00018_output['multi'][i][2])
                price.append(self.kiwoom.opw00018_output['multi'][i][3])
                earn.append(self.kiwoom.opw00018_output['multi'][i][4])
                ret.append(self.kiwoom.opw00018_output['multi'][i][5])
            mystocks = {'종목': name, '수량': num, '매입가': buy, '현재가': price, '평가손익': earn, '수익률(%)': ret}
            mystocks = DataFrame(mystocks)
            mystocks = mystocks.set_index(['종목'])

        #last 보고
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 프로그램이 종료되었습니다.")
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "\n프로그램이 종료되었습니다.\n총 TR 요청 횟수 : %d회\n -----계좌현황-----\n%s\n -----보유종목-----\n%s" % (self.tr, myaccount, mystocks))
        time.sleep(3)


    #상태표시줄(현재시간, 서버연결상태)
    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버가 연결되었습니다."
        else:
            state_msg = "서버가 연결되지 않았습니다."

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance() #계좌정보 실시간 조회

    def timeout3(self):
        if self.ts_1_p == 'True': #매수전략1 진행시 30초마다 조회
            self.volume_check()

    def timeout4(self):
        self.sell_stocks() #매도전략

    def timeout5(self): #9시 이후에 급등주알고리즘 시작
        market_start_time = QTime(9, 5, 0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.volume_start == 'false':
            self.volume_start = 'true'
            self.trading_strategy_1()

    def timeout7(self): #중간보고
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(1)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
        self.tr += 1

        bb = self.kiwoom.opw00018_output['single']
        myaccount = '총매입금액: %s원\n총평가금액: %s원\n총평가손익금액: %s원\n총수익률(%%): %s\n추정예탁자산: %s원' % (bb[0], bb[1], bb[2], bb[3], bb[4])
        print(myaccount)
        a = len(self.kiwoom.opw00018_output['multi'])
        if a != 0:
            name = []
            num = []
            buy = []
            price = []
            earn = []
            ret = []
            for i in range(a):
                name.append(self.kiwoom.opw00018_output['multi'][i][0])
                num.append(self.kiwoom.opw00018_output['multi'][i][1])
                buy.append(self.kiwoom.opw00018_output['multi'][i][2])
                price.append(self.kiwoom.opw00018_output['multi'][i][3])
                earn.append(self.kiwoom.opw00018_output['multi'][i][4])
                ret.append(self.kiwoom.opw00018_output['multi'][i][5])
            mystocks = {'종목': name, '수량': num, '매입가': buy, '현재가': price, '평가손익': earn, '수익률(%)': ret}
            mystocks = DataFrame(mystocks)
            mystocks = mystocks.set_index(['종목'])
        print(mystocks)
        # 중간보고
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 중간보고 완료.")
        print('hi')
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "\n--------중간보고--------\n총 TR 요청 횟수 : %d회\n --------계좌현황--------\n%s\n --------보유종목--------\n%s" % (self.tr, myaccount, mystocks))

    #종목명 나타내기
    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    #현금주문(수동주문)
    def send_order(self):
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText()
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        num = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price,
                               hoga_lookup[hoga], "")
        self.tr += 1

    #계좌정보
    def check_balance(self):

        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        self.tr += 1
        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
        self.tr += 1

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents()
        print('잔고조회완료')

    #거래량급증 거래전략1
    def trading_strategy_1(self):

        if self.ts_1_p == 'False':
            print('ts_1_p = true, 매수전략1 실행중입니다.')
            self.ts_1_p = 'True'
            self.label_7.setText("진행중...")
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 매수전략1 시작되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 매수전략1 시작되었습니다.")
            self.volume_check()

        elif self.ts_1_p == 'True':
            print('ts_1_p = False, 매수전략1 중지되었습니다.')
            self.label_7.setText("")
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 매수전략1 중지되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 매수전략1 중지되었습니다.")
            self.ts_1_p = 'False'

    #매수,매도주문
    def order_stocks(self,bs,code,num,price,set_price):

        '''
        :param bs: 매수=1 매도=2
        :param code: 종목코드
        :param num: 수량
        :param price: 가격 (시장가이면 0)
        :param set_price: 지정가=00 시장가=03
        :return:
        '''
        account = self.comboBox.currentText()

        # order
        self.kiwoom.send_order("send_order_req", "0101", account, bs, code, num, price, set_price, "")
        self.tr += 1

    #거래량급증 조회
    def volume_check(self):
        market_list = ['kospi', 'kosdaq']
        print('조회수급등조회시작')
        for market in market_list:
            if market == 'kospi':
                url = 'https://finance.naver.com/sise/sise_quant_high.nhn'
            elif market == 'kosdaq':
                url = 'https://finance.naver.com/sise/sise_quant_high.nhn?sosok=1'
            html = requests.get(url).text

            df = pd.DataFrame()
            df = df.append(pd.read_html(html, header=0)[1])
            df = df.dropna()
            df = df.rename(
                columns={'N': 'num', '증가율': 'rate', '종목명': 'name', '현재가': 'price', '전일비': 'diff', '등락률': 'updown',
                         '매수호가': 'buy_hoga',
                         '매도호가': 'sell_hoga', '거래량': 'volume', '전일거래량': 'yes_volume', 'PER': 'PER'})
            df = df.set_index(['num']) #크롤링완료

            #700이상
            df700 = df[[a > 700 for a in df.rate]]
            a700 = list(df700['name'])
            if len(df700) != 0:
                for i in range(len(df700)):
                    a = html.find(a700[i])
                    code = html[a-22:a-16]
                    self.list700.append(code)

            #교집합 구하기
            aa = set(self.list700)
            bb = set(self.list600)
            buy_set = aa & bb
            buy_set = list(buy_set)
            if len(buy_set) != 0:
                for i in range(len(buy_set)):
                    self.buy_list.append(buy_set[i])

            #600~700
            self.list600 = []
            df600 = df[[a > 400 and a < 700 for a in df.rate]]
            a600 = list(df600['name'])
            if len(df600) != 0:
                for i in range(len(df600)):
                    a = html.find(a600[i])
                    code = html[a - 22:a - 16]
                    self.list600.append(code)

        print('매수리스트: %s' % self.buy_list)

        #order
        if len(self.buy_list) == 0:
            pass
        else:
            account_number = self.comboBox.currentText()
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
            buy_q = int(self.kiwoom.d2_deposit[:-3].replace(',',''))
            buy_q = (buy_q//len(self.buy_list))//5 #예수금/선정종목갯수/5
            self.tr += 1

            for code in self.buy_list:
                time.sleep(0.5)
                self.kiwoom.set_input_value("종목코드", code)
                self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                self.tr += 1

                self.order_stocks(1,code, buy_q, 0, '03')
                self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매수주문\n종목: %s\n수량: %d\n가격: 시장가' % (self.kiwoom.stock_name, buy_q))
                self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString('hh:mm:ss') + 'ㅣ매수주문\n 종목: %s\n수량: %d\n가격: 시장가' %(self.kiwoom.stock_name, buy_q))
        self.buy_list = []
        self.list700 = []
        print("거래량급증조회완료")


    #목표수익률 도달시 팔기
    def sell_stocks(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(1)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
        self.tr += 1

        list_1 = list(self.kiwoom.opw00018_output['multi'])
        a = len(list_1)
        if a != 0:
            print('보유종목현황: %s' % list_1)
            for i in range(a):
                if float(list_1[i][5]) > 5:
                    code = list_1[i][6]
                    num = int(list_1[i][1].replace('.00','').replace(',',''))
                    self.kiwoom.set_input_value("종목코드", code)
                    self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                    self.tr += 1
                    self.order_stocks(2, code, num, 0, '03')
                    print('매도종목: %s' % code)
                    self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n 종목: %s\n수량: %d\n가격: 시장가' % (self.kiwoom.stock_name, num))
                    self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n 종목: %s\n수량: %d\n가격: 시장가' % (self.kiwoom.stock_name, num))
                elif float(list_1[i][5]) < -3:
                    code = list_1[i][6]
                    num = int(list_1[i][1].replace('.00', '').replace(',', ''))
                    self.kiwoom.set_input_value("종목코드", code)
                    self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                    self.tr += 1
                    print('매도종목: %s' % code)
                    self.order_stocks(2, code, num, 0, '03')
                    self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n 종목: %s\n수량: %d\n가격: 시장가' % (self.kiwoom.stock_name, num))
                    self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n 종목: %s\n수량: %d\n가격: 시장가' % (self.kiwoom.stock_name, num))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()


