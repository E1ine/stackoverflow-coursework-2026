import requests
import pandas as pd
import time
from datetime import datetime, timedelta

'''Параметры сбора данных'''
API_KEY = 'rl_2jY6ERvvAhoPnVCNGk4WFyCY1'

BASE_URL = "https://api.stackexchange.com/2.3/questions"

RAW_PARAMS = {
    'pagesize': 100, # 100 вопросов за раз (это максимум)
    'order': 'desc', # Сначала новые
    'sort': 'creation', # 25-26 года
    'site': 'stackoverflow',  # Основной сайт
    'key': API_KEY, # API-ключ 30к/день
    }

'''Функция для сбора сырых данных'''
def fetch_raw_questions(max_questions=20000): # лимит вопросов
    print(f"Собираю {max_questions} сырых данных...")

    all_data = [] # список для всех вопросов (накопитель будет 20000)
    page = 1 # начинаем с 1 страницы (счетчик страниц)

    while len(all_data) < max_questions: # пока меньше 20000 вопросов продолжаем
        params = RAW_PARAMS.copy() # копирование базовых параметров
        params['page'] = page # меняем номер страницы

        print(f"Страница {page} из ~{max_questions//100}...")

        response = requests.get(BASE_URL, params=params) # http запрос сылка автоматически обновляется

        if response.status_code != 200: # проверка статуса
            print(f"Ошибка API: {response.status_code}")
            break

        json_data = response.json() # запись данных(были строкой) в Python словарь в формате JSON

        if 'items' not in json_data:# вернет ошибку если придет без ключа items
            print("API вернул ошибку!")
            break
        if not json_data['items']:  #вернет ошибку если придет пустой список items (когда кончаются свежие вопросы)
            print("Данных больше нет")
            break

        all_data.extend(json_data['items']) # все проверки прошли -> добавляем в список 100 вопросов 
        page += 1 # переход на следующую страницу
        time.sleep(0.2) # задержка для того что бы не привысить 300запросов/мин, не перегрузить сервер и некоторые запросы не падали
    
    print(f"Собранно {len(all_data)} вопросов")
    return all_data # возвращаем 100 вопросов в переменную
'''Функция сохранения данных в .csv'''
def save_raw_dataset():
    print("Создание общего файла...")
    
    raw_data = fetch_raw_questions(20000) # возвращает список из 20к вопросов
    df = pd.DataFrame(raw_data) # делаем из списка таблицу с помощью Pandas

    filename = f'stackoverflow_raw_{len(df)}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv' # задаем умное название файлу префикс->кол-во строк->дата_время создания->расширение
    
    df.to_csv(filename, index=False)
    print(f"Готово!!! {filename}")
    print(f"{len(df)} строк, {len(df.columns)} колонок")
    return df, filename

if __name__ == "__main__": # конструкция которая говорит что это главный файл, начинай скачивание и при импортах функции доступны, но скачивание не произойдет повторно
    df, filename = save_raw_dataset()
    print("\n ДАННЫЕ ГОТОВЫ!")