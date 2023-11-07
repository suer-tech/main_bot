import datetime
import json
import os
import time
import binance
import emoji
import requests
import time
from binance.client import Client
from binance.um_futures import UMFutures
from urllib3.exceptions import ReadTimeoutError
import threading


limit = 500
median_x = 3
buy_sell_ratio_x = 7


# Переводим время в удобочитаемый вид-----------------------------------------------------------------------------
def convert_time(timestamp):
    timestamp_seconds = timestamp / 1000
    dt = datetime.datetime.fromtimestamp(timestamp_seconds, tz=datetime.timezone.utc)
    return (dt.strftime("%Y-%m-%d %H:%M:%S %Z"))

# Запрос обьемов с биржи-----------------------------------------------------------------------------
def get_buy_sell_ratio(symbol, interval, limit):
    url = "https://fapi.binance.com/futures/data/takerlongshortRatio"
    params = {
        "symbol": symbol,
        "period": interval,
        "limit": limit,
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error occurred while retrieving Kline data:", response.text)
        return None

# Запрос свечек с биржи-----------------------------------------------------------------------------
def get_kline_data(symbol, interval, limit=500, startTime=None, endTime=None):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
        "startTime": startTime,
        "endTime": endTime
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error occurred while retrieving Kline data:", response.text)
        return None

# Считаем высоту свечи в %-----------------------------------------------------------------------------
def check_diff_procent(sym, interval, limit):
    high = []
    low = []

    kline_data = get_kline_data(sym, interval, limit)

    for k in kline_data:
        # Process the Kline data
        high.append({kline_data[kline_data.index(k)][0]: kline_data[kline_data.index(k)][2]})
        low.append({kline_data[kline_data.index(k)][0]: kline_data[kline_data.index(k)][3]})

    # Преобразуем данные в словари для удобства обработки
    high_dict = {key: float(value) for item in high for key, value in item.items()}
    low_dict = {key: float(value) for item in low for key, value in item.items()}
    # Создаем список словарей с нужной структурой
    result = [{timestamp: round((high_dict[timestamp] - low_dict[timestamp]) / high_dict[timestamp] * 100, 4)} for timestamp in high_dict]

    return result

# Считаем среднюю высоту свечи в % за период limit-----------------------------------------------------------------------------
def calculate_median(data_list):
    # Шаг 1: Получить список значений из словарей
    values = [float(list(item.values())[0]) for item in data_list]

    # Шаг 2: Отсортировать список значений
    sorted_values = sorted(values)

    # Шаг 3: Найти медиану
    n = len(sorted_values)
    if n % 2 == 1:  # Если количество элементов нечетное
        median = sorted_values[n // 2]
    else:  # Если количество элементов четное
        mid_idx = n // 2
        median = (sorted_values[mid_idx - 1] + sorted_values[mid_idx]) / 2

    return median

# Считаем средний объем за период limit отсеиваем небольшие объемы-----------------------------------------------------------------------------
def calculate_central_tendency(data):
    # Step 1: Calculate the central tendency of 'buyVol' and 'sellVol'
    diff = buy_sell_ratio_x
    total_buy_vol = 0
    total_sell_vol = 0
    num_items = len(data)

    for item in data:
        total_buy_vol += float(item['buyVol'])
        total_sell_vol += float(item['sellVol'])

    mean_buy_vol = total_buy_vol / num_items
    mean_sell_vol = total_sell_vol / num_items

    # Step 2: Filter dictionaries with 'buyVol' and 'sellVol' greater than the calculated central tendency
    selected_items = []
    for item in data:
        buy_sell_ratio = float(item['buySellRatio'])
        buy_vol = float(item['buyVol'])
        sell_vol = float(item['sellVol'])
        if buy_vol > mean_buy_vol * diff or sell_vol > mean_sell_vol * diff:
                selected_items.append(item)

    # Step 3: Return selected dictionaries with the highest values

    return selected_items

# Находим высоту свечки и добавляем в словарь к данным о времени и обьемах свечи-----------------------------------------------------------------------------
def find_matching_dict(arr_1, arr_2):
    data = []
    for dict_1 in arr_1:
        timestamp_1 = dict_1['timestamp']
        for dict_2 in arr_2:
            timestamp_2 = list(dict_2.keys())[0]
            if timestamp_1 == timestamp_2:
                diff = list(dict_2.values())[0]
                new_dict = {'diff': diff}
                dict_1.update(new_dict)
                data.append(dict_1)
    return data

# Сравниваем высоту свечки с медианой и отсеиваем волотильные свечи-----------------------------------------------------------------------------
def compare_and_filter(find_dict, mediana):
    filtered_ratio = []

    for dict in find_dict:
        diff = dict["diff"]
        time = dict['timestamp']
        bsratio = dict['buySellRatio']
        if mediana * median_x > float(diff):
            f_ratio = {
                'time': time,
                'buySellRatio': bsratio
            }
            filtered_ratio.append(f_ratio)

    return filtered_ratio

def remove_elements_with_different_suffix(arr):
    i = 0
    while i < len(arr):
        if len(arr[i]) >= 4 and arr[i][-4:] != "USDT":
            arr.pop(i)
        else:
            i += 1

# Создаем файлы под запрос пользователя о позах-----------------------------------------------------------------------------
def createTxtFile(txt_file):
    try:
        f = open(txt_file, 'r')
    except FileNotFoundError as err:
        with open(txt_file, 'w') as fw:
            pass

def get_symbolPrice_ticker():
    url = "https://fapi.binance.com/fapi/v1/ticker/price"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error occurred while retrieving Kline data:", response.text)
        return None

# Инициализируем словарь для отслеживания состояния каждого актива и метку времени
signal_recorded = {}

# Функция для удаления устаревших записей
def clean_signal_recorded():
    while True:
        current_time = time.time()
        expiration_time = 15 * 60  # 15 минут (или другой интервал, который вам нужен)
        for symbol, timestamp in list(signal_recorded.items()):
            if current_time - timestamp > expiration_time:
                del signal_recorded[symbol]
        time.sleep(60)  # Проверка каждую минуту

# Создаем и запускаем поток для удаления устаревших записей
cleaner_thread = threading.Thread(target=clean_signal_recorded)
cleaner_thread.daemon = True
cleaner_thread.start()


# Создаем файлы для оповещения по сигналу
createTxtFile('signal_vol.txt')


while True:
    index = []
    select = []
    try:
        symb_index = get_symbolPrice_ticker()
        for symb in symb_index:
            if symb['symbol'].endswith('USDT'):
                index.append(symb['symbol'])
        print(len(index))

        for sym in index:
            try:
                ratio = get_buy_sell_ratio(sym, '1h', limit)
                selected_dictionaries = calculate_central_tendency(ratio)
                diff_procent = check_diff_procent(sym, '1h', limit)
                find_dict = find_matching_dict(selected_dictionaries, diff_procent)
                mediana = calculate_median(diff_procent)
                filtered_ratio = compare_and_filter(find_dict, mediana)

                for find in find_dict:
                    if mediana * median_x > float(find['diff']):
                        select.append(find)

                signal = select[-1]

            #
            except ZeroDivisionError as err:
                continue
            except IndexError as err:
                continue
            #
            this_time = datetime.datetime.now()  # Получаем текущее время
            time_signal = datetime.datetime.strptime(convert_time(signal['timestamp']), "%Y-%m-%d %H:%M:%S %Z")

            t_vol = this_time - time_signal


            # Сигнал большого обьема----------------------------
            if t_vol.total_seconds() <= 4500:  # 900 секунд = 15 минут
                for symb in symb_index:
                    if symb['symbol'] == sym:
                        price = symb['price']
                        decimals = len(str(int(float(price))))

                        long = {
                            '1 tvh': round(float(price), decimals),
                            '2 tvh': round(float(price) - float(price) / 100 * 2, decimals),
                            '3 tvh': round(float(price) - float(price) / 100 * 4, decimals),
                            'stop': round(float(price) - float(price) / 100 * 5.5, decimals),
                            'take': round(float(price) + float(price) / 100 * 2, decimals),
                        }

                        short = {
                            '1 tvh': round(float(price), decimals),
                            '2 tvh': round(float(price) + float(price) / 100 * 2, decimals),
                            '3 tvh': round(float(price) + float(price) / 100 * 4, decimals),
                            'stop': round(float(price) + float(price) / 100 * 5.5, decimals),
                            'take': round(float(price) - float(price) / 100 * 2, decimals),
                        }

                with open('signal_vol.txt', 'w', encoding='utf-8') as fw:
                    mess = f"{emoji.emojize(':antenna_bars:Скачок объема торгов')}\n{emoji.emojize(':check_mark_button:')}{sym}\n"
                    fw.write(mess)
                    fw.write(f"\nLong\n")
                    for key, value in long.items():
                        fw.write(f"{key}: {value}\n")

                    fw.write(f"\nShort\n")
                    for key, value in short.items():
                        fw.write(f"{key}: {value}\n")
                print(sym, convert_time(signal['timestamp']))
                # Устанавливаем флаг как метку времени текущего актива
                signal_recorded[sym] = time.time()


    except binance.error.ClientError as err:
        print('ReduceOnly Order is rejected')
        with open('error.txt', 'w') as fw:
            json.dump('ReduceOnly Order is rejected', fw)
            time.sleep(3)
            pass
        time.sleep(5)
    # except requests.exceptions.ConnectionError as err:
    #     print('Connection reset by peer')
    #     with open('error.txt', 'w') as fw:
    #         json.dump('Connection reset by peer', fw)
    #         time.sleep(3)
    #         pass
    #     time.sleep(5)
    # except binance.error.ServerError as err:
    #     print('binance.error.ServerError')
    #     with open('error.txt', 'w') as fw:
    #         json.dump('binance.error.ServerError', fw)
    #         time.sleep(3)
    #         pass
    #     time.sleep(5)
    #
    # except TypeError as err:
    #     print('TypeError')
    #     with open('error.txt', 'w') as fw:
    #         json.dump('TypeError', fw)
    #         time.sleep(3)
    #         pass
    #     time.sleep(5)
    # except ReadTimeoutError as err:
    #     print('ReadTimeoutError')
    #     with open('error.txt', 'w') as fw:
    #         json.dump('ReadTimeoutError', fw)
    #         time.sleep(3)
    #         pass
    #     time.sleep(5)
    # except json.decoder.JSONDecodeError as err:
    #     print('json.decoder.JSONDecodeError')
    #     with open('error.txt', 'w') as fw:
    #         json.dump('json.decoder.JSONDecodeError', fw)
    #         time.sleep(3)
    #         pass
    #     time.sleep(5)








