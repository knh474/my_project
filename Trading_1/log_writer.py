import logging
import logging.handlers
from datetime import datetime

# 오늘 날짜 시 분 초 로그 저장
today_date = datetime.today().strftime('%Y-%m-%d %H_%M_%S')

# logger 인스턴스를 생성 및 로그 레벨 설정
log = logging.getLogger('TEST_LOGGER.')
log.setLevel(logging.DEBUG)

# formatter 생성
formatter = logging.Formatter('[ %(levelname)-10s | %(filename)s: %(lineno)s\t\t] %(asctime)s > %(message)s')

# 스트림 / 파일 로그 출력 핸들러
fileHandler = logging.FileHandler('./log/' + str(today_date) + '.log')
streamHandler = logging.StreamHandler()

# 스트림 / 파일 로그 출력 핸들러 + formatter
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)

# logger 인스턴스 + 핸들러
log.addHandler(fileHandler)
log.addHandler(streamHandler)

# logging
if __name__ == '__main__':
    log.debug('debug')
    log.info('info')
    log.warn('warn')
    log.warning('warning')
    log.error('error')
    log.critical('critical')
    log.fatal('fatal')


