import time
t= time.gmtime()

file_today = '{}-{}-{}'.format(t.tm_year, t.tm_mon, t.tm_mday)

code_list = ['01','02','03','04','05']

f = open(file_today+'.txt','a')
for code in code_list:
    f.write(code+'\n')
f.close()

f = open(file_today+'.txt','r')
a = f.readlines()
f.close()
list = []
for code in a:
    list.append(code[:2])



print(list)

if '03' in list:
    print('매수된종목')
elif '03' not in list:
    print('매수안된종목')
