import pandas as pd
import glob
import os

print("Объеденяем все данные...")

'''Считывание всех stackoverflow_raw_'''
csv_files = glob.glob('*stackoverflow_raw_*.csv') + glob.glob('data/*stackoverflow_raw_*.csv') # Список всех csv
print(f"Всего файлов {len(csv_files)}")

dfs = [] # Пустой список для таблиц
for file in csv_files:
    df = pd.read_csv(file) # Считываем csv -> таблица
    print(f"Загружен {file}: {len(df)} строк")
    dfs.append(df) # Добавляем список

'''Объеденение и удаление дубликатов по question_id'''
df_combined = pd.concat(dfs, ignore_index=True) # Склеивает все таблицы (одна под другой) без дыр
df_unique = df_combined.drop_duplicates(subset=['question_id']) # Убирает одинаковые вопросы

df_final = df_unique.sort_values('creation_date', ascending=False) # Сортирует по дате(новые сверху)

'''Сохранение единого датасета'''
output_file = 'data/stackoverflow_coursework_final.csv' # Задаем имя финальному файлу
df_final.to_csv(output_file, index=False) # Сохраняет в единый CSV не сохраняет номера строк

print(f"Итого {len(df_final)} уникальных вопросов")
print(f"Сохранено в: {output_file}")
print("\n Первые строки:")
print(df_final.head())