import time
import functions


starttime = time.time()
timeout = time.time() + 60 * 60 * 12  # работа скрипта ограничена 12 часами(переводим в секунды)
counterr = 1

while time.time() <= timeout:
    try:
        functions.prt("Скрипт работает, время: "+ time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(time.time())))
        functions.main(counterr)
        counterr = counterr + 1
        if counterr > 5:
            counterr = 1
        time.sleep(60 - ((time.time() - starttime) % 60.0)) # интервал одна минута
    except KeyboardInterrupt:
        print('\n\\Скрипт остановлен')
        exit()