import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from Kiwoom import *
import pandas as pd
import telegram
import requests
import os
from log_writer import *

'''
 ########################### 패치노트 ###########################
 *현재버전: 0.4.3
 *API 서버 점검시간: 월~토 4:55~5:00, 일 4:00~4:30
 0.4.1 9.27_01 
 -데이터프레임 empty면 실행 안하기
 0.4.2 9.27_02 
 -프로그램 시작, 종료 시 날짜 출력
 -매도주문 현재가 표시
 -급증률 700기준 잡기
 0.4.3 9.29_01
 -종목 앞글자 이름 같을 때 종목리스트 출력 오류 보완(volume_check)
 -목표수익률 3%, 손절 2.5% 수정
 -전체자산의 5% 매수로 수정
 -로깅 모듈 추가
 ################################################################
 '''


form_class = uic.loadUiType("trader 0.3.ui")[0]

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
        self.market_start = 'false' #마켓 초기값
        self.market_close = 'false'
        self.shutdown_0900 = 'false'
        self.shutdown_1530 = 'false'

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
        self.timer5 = QTimer(self)
        self.timer5.start(1000 * 15)  # 60초 09:00~15:30 장중모드
        self.timer5.timeout.connect(self.timeout5)

        # Timer7
        self.timer7 = QTimer(self)
        self.timer7.start(1000 * 1800)  # 30분 중간보고, 장마감후 어플 및 컴퓨터 종료
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
        self.pushButton_5.clicked.connect(self.timeout7)  # 테스트버튼

        #계좌정보
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItems(accounts_list)

        #프로그램시작알림
        log.info('프로그램이 시작되었습니다.')
        self.textEdit.append('\n' + QDateTime.currentDateTime().toString("yyyy/MM/dd\nhh:mm:ss") +"ㅣ 프로그램이 시작되었습니다.")
        self.mybot.sendMessage(self.chat_id, text='\n' + QDateTime.currentDateTime().toString("yyyy/MM/dd\n hh:mm:ss") + "ㅣ 프로그램이 시작되었습니다.")
        self.get_etf_etn_list()  # ETN, ETF 종목 리스트 저장

    #종료
    def quit_app(self):
        log.info('프로그램이 종료되었습니다.')
        if self.ts_1_p == 'True':
            self.trading_strategy_1()
        self.timer.stop()
        self.timer2.stop()
        self.timer3.stop()
        self.timer4.stop()
        self.timer5.stop()
        self.timer7.stop()
        time.sleep(1)

        #계좌정보요청
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        mystocks = ''

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
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 프로그램이 종료되었습니다.\n총 TR 요청 횟수 : %d회\n --------계좌현황--------\n계좌번호: %s\n%s\n --------보유종목--------\n%s"
                                                  % (self.tr,account_number, myaccount, mystocks))
        with open('log.txt','a') as f:
            f.writelines(self.textEdit.toPlainText())
        time.sleep(3)



    #상태표시줄(현재시간, 서버연결상태)
    def timeout(self):
        market_start_time = QTime(9, 00, 00)
        market_close_time = QTime(15, 30, 00)
        market_start_time2 = QTime(9, 00, 2)
        market_close_time2 = QTime(15, 30, 2)
        current_time = QTime.currentTime()


        # 9시 이후에 급등주알고리즘 시작
        if current_time > market_start_time and current_time < market_start_time2 and self.market_start == 'false':
            log.info('장 시작 알림')
            self.market_start = 'true'
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장이 시장되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장이 시작되었습니다.")
        elif current_time > market_close_time and current_time < market_close_time2 and self.market_close == 'false':
            log.info('장 종료알림')
            self.market_close = 'true'
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장이 종료되었습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장이 종료되었습니다.")

        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버가 연결되었습니다."
        else:
            state_msg = "서버가 연결되지 않았습니다."
            log.fatal('서버 미연결')
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ서버가 연결되지 않았습니다.")
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 서버가 연결되지 않았습니다.")

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance() #계좌정보 실시간 조회

    def timeout3(self):
        if self.ts_1_p == 'True': #매수전략1 진행시 30초마다 조회
            log.debug('거래량조회 알고리즘 실행')
            self.volume_check()

    def timeout4(self):
        log.debug('매도 알고리즘 실행')
        self.sell_stocks() #매도전략

    def timeout5(self):

        if self.checkBox_2.isChecked():

            market_start_time = QTime(9, 3, 00)
            market_close_time = QTime(15, 40, 00)
            current_time = QTime.currentTime()

            # 9시 이후에 급등주알고리즘 시작
            if current_time > market_start_time and self.shutdown_0900 =='false' and self.ts_1_p =='False':
                log.info('장이 시작되어 매수알고리즘 실행')
                self.shutdown_0900 = 'true'
                self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장 시작, 매수전략1 시작하겠습니다.")
                self.mybot.sendMessage(self.chat_id,
                                       text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 장 시작, 매수전략1 시작하겠습니다.")
                self.trading_strategy_1()

            #15시 40 분 이후 알고리즘 중지 및 10분 뒤 컴퓨터 종료
            elif current_time > market_close_time and self.shutdown_1530 =='false':
                log.info('장이 종료되어 알고리즘 중지')
                self.shutdown_1530 = 'true'
                self.trading_strategy_1()
                time.sleep(1)
                self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 10분 후 컴퓨터를 종료합니다.")
                self.mybot.sendMessage(self.chat_id,
                                       text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 10분 후 컴퓨터를 종료합니다.")
                log.fatal('컴퓨터 종료 카운트 시작')

                self.quit_app()
                time.sleep(10)
                os.system("shutdown -s -t 600")
                print('10분 후 컴퓨터를 종료합니다...')

    def timeout7(self): #중간보고
        log.debug('중간보고')
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(1)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
        self.tr += 1
        mystocks = ''
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
        time.sleep(1)
        # 중간보고
        self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 중간보고 완료.")
        self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") +
                                                  "\n--------중간보고--------\n총 TR 요청 횟수 : %d회\n --------계좌현황--------\n계좌번호: %s\n%s\n --------보유종목--------\n%s"
                                                  % (self.tr, account_number, myaccount, mystocks))

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
        log.debug('잔고조회')
        self.kiwoom.reset_opw00018_output()
        account_number = self.comboBox.currentText()
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(1)
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


    #거래량급증 거래전략1
    def trading_strategy_1(self):
        log.info('매수전략1 실행/중지')
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
        log.critical('주문실행')
        # order
        self.kiwoom.send_order("send_order_req", "0101", account, bs, code, num, price, set_price, "")
        self.tr += 1

    #거래량급증 조회
    def volume_check(self):

        print('조회수급등조회시작')
        kospi_url = 'https://finance.naver.com/sise/sise_quant_high.nhn'
        kosdaq_url = 'https://finance.naver.com/sise/sise_quant_high.nhn?sosok=1'

        df = pd.DataFrame()

        html_1 = requests.get(kospi_url).text
        df = df.append(pd.read_html(html_1, header=0)[1])
        html_2 = requests.get(kosdaq_url).text
        df = df.append(pd.read_html(html_2, header=0)[1])
        df = df.dropna()
        df = df.rename(
                    columns={'N': 'num', '증가율': 'rate', '종목명': 'name', '현재가': 'price', '전일비': 'diff', '등락률': 'updown',
                             '매수호가': 'buy_hoga',
                             '매도호가': 'sell_hoga', '거래량': 'volume', '전일거래량': 'yes_volume', 'PER': 'PER'})
        df = df.set_index(['num']) #크롤링완료
        html = html_1 + html_2
        if df.empty is True:
            log.debug('네이버금융 데이터가 없음')
            self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 네이버금융 데이터가 없습니다.')
            self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString(
                'hh:mm:ss') + 'ㅣ 네이버금융 데이터가 없습니다.')
            print('네이버금융 데이터가 없습니다.')
        else:

            # 0.4.1 수정
            #700이상
            df700 = df[[a > 700 for a in df.rate]]
            a700 = list(df700['name'])
            if len(df700) != 0:
                for i in range(len(df700)):
                    # 0.4.3 수정(종목이름 앞글자 같을 때 보완)
                    a = html.find(a700[i])
                    b = len(a700[i])
                    if html[a + b] == '<':
                        code = html[a - 22:a - 16]
                        self.list700.append(code)
                    else:
                        html = html[a + b:]
                        a = html.find(a700[i])
                        code = html[a - 22:a - 16]
                        self.list700.append(code)
            print(self.list700)
            print(self.list600)

            #교집합 구하기
            aa = set(self.list700)
            bb = set(self.list600)
            buy_set = aa & bb
            buy_set = list(buy_set)
            if len(buy_set) != 0:
                for code in buy_set:
                    if code in self.etn_etf_list:
                        pass
                    else:
                        for i in range(len(buy_set)):
                            self.buy_list.append(buy_set[i])

            #600~700
            self.list600 = []
            df600 = df[[a < 700 for a in df.rate]]
            a600 = list(df600['name'])
            if len(df600) != 0:
                for i in range(len(df600)):
                    a = html.find(a600[i])
                    b = len(a600[i])
                    if html[a + b] == '<':
                        code = html[a - 22:a - 16]
                        self.list600.append(code)
                    else:
                        html = html[a + b:]
                        a = html.find(a600[i])
                        code = html[a - 22:a - 16]
                        self.list600.append(code)
            print('매수리스트: %s' % self.buy_list)


        #order
        #0.4.3 자산5%
        if len(self.buy_list) == 0:
            pass
        else:
            log.debug('바이리스트 주문을 시작함')
            self.kiwoom.reset_opw00018_output()
            account_number = self.comboBox.currentText()
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
            buy_q = int(self.kiwoom.opw00018_output['single'][4].replace(',', ''))//20 #추정예탁자산의 5%
            self.tr += 1
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
            d2_deposit = int(self.kiwoom.d2_deposit.replace(',', '')) #d2 예수금
            self.tr +=1

            if buy_q <= d2_deposit:
                log.critical('주문실행')
                for code in self.buy_list: #주문하기
                    #0.4.3 매수비중 5%제한
                    time.sleep(0.5)
                    self.kiwoom.set_input_value("종목코드", code)
                    self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                    buy_q = buy_q // self.kiwoom.stock_pv #매수금액/현재가 : 수량
                    self.tr += 1
                    time.sleep(1)
                    self.order_stocks(1, code, buy_q, 0, '03')
                    self.textEdit.append(
                        QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매수주문\n종목: %s\n수량: %d\n가격: 시장가\n현재가:%s' % (
                        self.kiwoom.stock_name, buy_q, self.kiwoom.stock_pv))
                    self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString(
                        'hh:mm:ss') + 'ㅣ매수주문\n 종목: %s\n수량: %d\n가격: 시장가\n현재가:%s' % (
                                                              self.kiwoom.stock_name, buy_q, self.kiwoom.stock_pv))


            else: #주문x
                log.critical('예수금이 부족해 주문하지 못함')
                self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + "ㅣ 예수금이 부족합니다.")
                self.mybot.sendMessage(self.chat_id,
                                       text=QTime.currentTime().toString("hh:mm:ss") + "ㅣ 예수금이 부족합니다.")
                print('예수금이 부족합니다.')

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
            log.debug('보유종목현황')
            print('보유종목현황: %s' % list_1)
            #0.4.3 3%, -2.5% 수정
            for i in range(a):
                if float(list_1[i][5]) > 3:
                    log.debug('이익실현매도')
                    code = list_1[i][6]
                    num = int(list_1[i][1].replace('.00','').replace(',',''))
                    self.kiwoom.set_input_value("종목코드", code)
                    self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                    self.tr += 1
                    time.sleep(1)
                    self.order_stocks(2, code, num, 0, '03')
                    print('매도종목: %s' % code)
                    self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 이익실현\n매도주문\n 종목: %s\n수량: %d\n가격: 시장가\n현재가: %s' % (self.kiwoom.stock_name, num,self.kiwoom.stock_pv))
                    self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n종목: %s\n수량: %d\n가격: 시장가\n현재가: %s' % (self.kiwoom.stock_name, num,self.kiwoom.stock_pv))
                elif float(list_1[i][5]) < -2.5:
                    log.debug('손절매도')
                    code = list_1[i][6]
                    num = int(list_1[i][1].replace('.00', '').replace(',', ''))
                    self.kiwoom.set_input_value("종목코드", code)
                    self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
                    self.tr += 1
                    time.sleep(1)
                    self.order_stocks(2, code, num, 0, '03')
                    print('매도종목: %s' % code)
                    self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 손절\n매도주문\n 종목: %s\n수량: %d\n가격: 시장가\n현재가: %s' % (self.kiwoom.stock_name, num,self.kiwoom.stock_pv))
                    self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ 매도주문\n종목: %s\n수량: %d\n가격: 시장가\n현재가: %s' % (self.kiwoom.stock_name, num, self.kiwoom.stock_pv))

    #ETF, ETN 종목 리스트 저장
    def get_etf_etn_list(self):
        log.debug('etf,etn리스트 저장')
        time.sleep(2)
        market_list = ['etn', 'etf']
        self.etn_etf_list = []

        for market in market_list:

            if market == 'etn':
                url = 'https://finance.naver.com/api/sise/etnItemList.nhn?'
            elif market == 'etf':
                url = 'https://finance.naver.com/api/sise/etfItemList.nhn?'
            html = requests.get(url).text
            aa = html.split('},')
            for stock in aa:
                code_start = stock.find('itemcode')
                code = stock[code_start + 11:code_start + 17]
                self.etn_etf_list.append(code)
        #print('ETN, ETF 종모리스트 저장 완료')
        #self.mybot.sendMessage(self.chat_id, text=QTime.currentTime().toString("hh:mm:ss") + 'ㅣ ETF, ETN 종목리스트 저장 완료')
        #self.textEdit.append(QTime.currentTime().toString("hh:mm:ss") + 'ㅣ ETF, ETN 종목리스트 저장 완료')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()


