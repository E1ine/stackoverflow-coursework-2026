# 🎓 StackOverflow Курсовая 2026

## 📊 Быстрый старт (2 минуты)

**ШАГ 1: Клонируй проект**  
git clone https://github.com/E1ine/stackoverflow-coursework-2026  
cd stackoverflow-coursework-2026  

**ШАГ 2: Установи зависимости**  
pip install -r requirements.txt  

## 👥 Параллельная работа (Task1-Task5)

| Ветка | Задача |               |
|-------|--------|---------------|
| `Task1` | **Тренды тегов**   | |
| `Task2` | **Кластеризация**  | |
| `Task3` | **ML-прогнозы**    | |
| `Task4` | **Время ответа**   | |
| `Task5` | **Прокрастинация** | |

**📋 Алгоритм работы (КОПИРУЙ команды):**

**1. Обновись с main:**  
git checkout main && git pull origin main  

**2. Перейди в свою ветку:**  
git checkout TaskX  *// Task1, Task2, Task3, Task4 или Task5*  

**3. Сохрани изменения:**  
git add .  
git commit -m "Task№: описание"  
git push origin Task№  
---

## 📈 Данные готовы!   
```python
df = pd.read_csv('data/stackoverflow_coursework_final.csv')
print(df.shape)
