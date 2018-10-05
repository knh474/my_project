import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
from pandas import DataFrame,Series
import telegram

form_class = uic.loadUiType("trader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #텔레그램봇
        my_token = '692301814:AAEfmddhyZPcO0Uzh8r5ZehfooTPOvKOOqc'
        self.mybot = telegram.Bot(token=my_token)
        self.chat_id = 544924927

        self.kiwoom = Kiwoom() #키움인스턴스 생성
        self.kiwoom.comm_connect() #API로그인

        self.ts_1_p = 'False' #거래전략1 초기값

        # Timer1
        self.timer = QTimer(self)
        self.timer.start(1000) #1초
        self.timer.timeout.connect(self.timeout)

        # Timer2
        self.timer2 = QTimer(self)
        self.timer2.start(1000 * 10) #10초
        self.timer2.timeout.connect(self.timeout2)

        # Timer3
        self.timer3 = QTimer(self)
        self.timer3.start(1000 * 30) #30초
        self.timer3.timeout.connect(self.timeout3)


        # Timer4
        self.timer4 = QTimer(self)
        self.timer4.start(1000 * 33)  # 33초
        self.timer4.timeout.connect(self.timeout4)

        # Timer5
        self.timer5 = QTimer(self)
        self.timer5.start(1000 * 35)  # 35초
        self.timer5.timeout.connect(self.timeout5)

        # Timer6
        self.timer6 = QTimer(self)
        self.timer6.start(1000 * 37)  # 37초
        self.timer6.timeout.connect(self.timeout6)

        # Timer10
        self.timer4 = QTimer(self)
        self.timer4.start(1000 * 3600) #1시간 후 프로그램종료!
        self.timer4.timeout.connect(self.quit_app)
        self.timer4.timeout.connect(QCoreApplication.instance().quit)


        self.list700 = []
        self.list600700 = []

        self.lineEdit.textChanged.connect(self.code_changed) #종목코드 입력시
        self.pushButton.clicked.connect(self.send_order) #현금주문 버튼 클릭시
        self.pushButton_2.clicked.connect(self.check_balance) #계좌정보 조회
        self.pushButton_3.clicked.connect(self.trading_strategy_1) #거래전략1호
        self.pushButton_4.clicked.connect(self.quit_app) #앱종료
        self.pushButton_4.clicked.connect(QCoreApplication.instance().quit)  # 앱종료
        #계좌정보
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        self.load_buy_sell_list()

        #로그기록
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") +"ㅣ 프로그램이 시작되었습니다.")
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 프로그램이 시작되었습니다.")

    #종료
    def quit_app(self):
        self.timer = ''
        self.timer2 = ''
        self.timer3 = ''
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 프로그램이 종료되었습니다.")
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 프로그램이 종료되었습니다.")
        time.sleep(3)


    #상태표시줄(현재시간, 서버연결상태)
    def timeout(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버 연결되었습니다."
        else:
            state_msg = "서버가 연결되지 않았습니다."

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance() #계좌정보 실시간 조회

    def timeout3(self):
        if self.ts_1_p == 'True': #거래전략1 진행시 30초마다 조회
            self.volume_check()

    def timeout4(self):
        self.sell_stocks()
    def timeout5(self):
        self.load_buy_sell_list()
    def timeout6(self):
        self.trade_stocks()



    #로그파일 > txt파일로 저장
    def txt_changed(self):
        f = open('log.txt','a')
        log_text = self.textEdit.text
        f.write(log_text)
        f.close()

    #종목명 나타내기
    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    #현금주문
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
    #계좌정보
    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        #account_number = self.kiwoom.get_login_info("ACCNO")
        #account_number = account_number.split(';')[0]
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

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



    def load_buy_sell_list(self):
        f = open("buy_list.txt",'rt')
        buy_list = f.readlines()
        f.close()

        ff = open("sell_list.txt",'rt')
        sell_list = ff.readlines()
        ff.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_4.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(j, i, item)
        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_4.setItem(len(buy_list) + j, i, item)

        self.tableWidget_4.resizeRowsToContents()
        print('buy & sell.txt 불러오기')


    def trade_stocks(self):
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        # account
        account = self.comboBox.currentText()

        # buy list
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price,
                                       hoga_lookup[hoga], "")
                self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ ' + code + ' ' + num +'주 '+ price+ "원 매수주문")

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price,
                                       hoga_lookup[hoga], "")
                self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ ' + code + ' ' + num + '주 ' + price + "원 매도주문")

                # buy list
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "매수주문완료")

        # file update
        f = open("buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "매도주문완료")

        # file update
        f = open("sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()
        print('거래알고리즘실행완료')

    #거래량급증 거래전략1
    def trading_strategy_1(self):

        if self.ts_1_p == 'False':
            print('ts_1_p = true')
            self.ts_1_p = 'True'
            self.label_7.setText("진행중...")
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 전략1호 시작되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 전략1호 시작되었습니다.")
            self.volume_check()

        elif self.ts_1_p == 'True':
            print('ts_1_p = False')
            self.label_7.setText("")
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 전략1호 중지되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 전략1호 중지되었습니다.")
            self.ts_1_p = 'False'


    #거래량급증 조회
    def volume_check(self):
        print('거래량급등조회시작')
        self.kiwoom.reset_opt10023_output()

        self.kiwoom.set_input_value("시장구분", 000)
        self.kiwoom.set_input_value("시간구분", 2)
        self.kiwoom.set_input_value("정렬구분", 2)
        self.kiwoom.set_input_value("거래량구분", 5)
        self.kiwoom.set_input_value("시간", "")
        self.kiwoom.set_input_value("종목조건", 0)
        self.kiwoom.set_input_value("가격구분", 0)
        self.kiwoom.comm_rq_data("opt10023_req", "opt10023", 0, "0168")

        while self.kiwoom.remained_data == True:
            time.sleep(TR_REQ_TIME_INTERVAL)
            self.kiwoom.set_input_value("시장구분", 000)
            self.kiwoom.set_input_value("시간구분", 2)
            self.kiwoom.set_input_value("정렬구분", 2)
            self.kiwoom.set_input_value("거래량구분", 5)
            self.kiwoom.set_input_value("시간", "")
            self.kiwoom.set_input_value("종목조건", 0)
            self.kiwoom.set_input_value("가격구분", 0)
            self.kiwoom.comm_rq_data("opt10023_req", "opt10023", 2, "0168")

        df = DataFrame(self.kiwoom.opt10023_output) #거래급증종목 데이터프레임으로 받음
        print(df)
        df700 = df[[a > 700 for a in df.volume]] #700이상 종목
        self.list700 = list(df700['code'])
        #print('700이상: ' + self.list700)
        aa = set(self.list700)
        bb = set(self.list600700)
        buy_set = aa & bb
        buy_set = list(buy_set)
        df600 = df[[a > 600 for a in df.volume]]
        df600700 = df600[[a < 700 for a in df600.volume]]

        self.list600700 = []
        self.list600700 = list(df600700['code'])
        #print('600이상700미만: ' + self.list600700)

        #buy_list 업데이트
        if len(buy_set) == 0:
            pass
        else:
            #print('buy_list: ' + buy_set)
            account_number = self.comboBox.currentText()
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
            buy_q = int(self.kiwoom.d2_deposit[:-3].replace(',',''))
            buy_q = (buy_q//len(buy_set))//5

            f = open("buy_list.txt", "a")
            for code in buy_set:
                time.sleep(0.2)
                self.kiwoom.set_input_value("종목코드", code)
                self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                self.mybot.sendMessage(self.chat_id, text="매수선정종목: " + self.kiwoom.stock_name)
                f.write("매수;%s;시장가;%d;0;매수전\n" % (code, buy_q // self.kiwoom.stock_pv))
                print('buy_list.txt updated')
            f.close()

        self.list700 = []
        print("거래량급증조회완료")


    #목표수익률 도달시 팔기
    def sell_stocks(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")



        print('보유종목현황: ' + self.kiwoom.opw00018_output['multi'])
        list_1 = list(self.kiwoom.opw00018_output['multi'])
        a = len(list_1)
        f = open('sell_list.txt', 'a')
        for i in range(a):
            if float(list_1[i][5]) > 5:
               f.write("매도;%s;시장가;%s;0;매도전\n" % (list_1[i][6], list_1[i][1]))
            elif float(list_1[i][5]) < -2:
                f.write("매도;%s;시장가;%s;0;매도전\n" % (list_1[i][6], list_1[i][1]))
        f.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()


