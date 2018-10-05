import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
from pandas import DataFrame

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    #키움API 컨트롤
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    #시그널 연결
    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)

    #로그인창
    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        #이벤트루프에 진입하여 이벤트 발생 전까지 종료되지 않음
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    #로그인 로그
    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 되었습니다.")
        else:
            print("로그아 웃되었습니다.")

        self.login_event_loop.exit()

    #입력값
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    #자료전송
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    #자료요청
    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    #반환받은 데이터의 개수
    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    #자료수신
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10023_req":
            self._opt10023(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        elif rqname == "opt10001_req":
            self._opt10001(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    #접속상태
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    #주문
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    #체결잔고
    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    #체결잔고데이터 수신
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        #개발가이드 8.19절
        #print(gubun)
        #print(self.get_chejan_data(9203)) #주문번호
        print(self.get_chejan_data(302)) #종목명
        print(self.get_chejan_data(900)) #주문수량
        #print(self.get_chejan_data(901)) #주문가격

    #로그인정보
    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    #종목리스트 받아오기
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    #종목명 알아오기
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    #실투/모투 구분
    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    # 거래량급증
    def _opt10023(self, rqname, trcode):
        rows = self._get_repeat_cnt(trcode, rqname)

        for i in range(rows):
            code = self._comm_get_data(trcode, "", rqname, i, "종목코드")
            volume_rate = self._comm_get_data(trcode, "", rqname, i, "급증률")

            self.opt10023_output['code'].append(code)
            self.opt10023_output['volume'].append(float(volume_rate))

    #예수금(d+2)
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    #종목현재가 등 정보
    def _opt10001(self, rqname, trcode):
        stock_pv = self._comm_get_data(trcode, "", rqname, 0, "현재가")
        if stock_pv[0] == '+':
            self.stock_pv = int(stock_pv[1:])
        elif stock_pv[0] == '-':
            self.stock_pv = int(stock_pv[1:])
        self.stock_name = self._comm_get_data(trcode, "", rqname, 0, "종목명")

    #잔고 정보
    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format3(total_earning_rate)

        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate)
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")
            code = self._comm_get_data(trcode, "", rqname, i, "종목번호")
            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)
            code = code[1:]
            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price,
                                                  eval_profit_loss_price, earning_rate, code])

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def reset_opt10023_output(self):
        self.opt10023_output = {'code': [],'volume':[]}

    #천의자리 콤마
    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'

        format_data = format(float(strip_data), ',.0f')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    @staticmethod
    def change_format3(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'

        format_data = format(float(strip_data), ',.2f')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom() #인스턴스 생성
    kiwoom.comm_connect() #로그인 실행

    #Test
    kiwoom.reset_opw00018_output()
    account_number = '8107606811'
    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
    buy_q = int(kiwoom.opw00018_output['single'][4].replace(',', '')) // 20  # 추정예탁자산의 5%
    print(buy_q)
    kiwoom.set_input_value("계좌번호", account_number)
    kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")
    d2_deposit = int(kiwoom.d2_deposit.replace(',', ''))  # d2 예수금
    print(d2_deposit)
