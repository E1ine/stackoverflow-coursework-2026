#!/usr/bin/env bash
# =============================================================================
#  setup.sh — Автоматический запуск stackoverflow-coursework-2026
#  Использование:
#    chmod +x setup.sh
#    ./setup.sh              # полная установка + все задачи
#    ./setup.sh --only-analytics  # только аналитика (БД уже настроена)
#    ./setup.sh --task 4     # запустить только одну задачу
# =============================================================================

set -euo pipefail

# ─── Цвета ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Helpers ─────────────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}━━━  $*  ━━━${RESET}"; }

# ─── Аргументы ───────────────────────────────────────────────────────────────
ONLY_ANALYTICS=false
SINGLE_TASK=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --only-analytics) ONLY_ANALYTICS=true; shift ;;
        --task)           SINGLE_TASK="$2"; shift 2 ;;
        -h|--help)
            echo "Использование: $0 [--only-analytics] [--task 1-5]"
            exit 0
            ;;
        *) error "Неизвестный аргумент: $1" ;;
    esac
done

# ─── Константы ───────────────────────────────────────────────────────────────
REPO_URL="https://github.com/E1ine/stackoverflow-coursework-2026"
REPO_DIR="stackoverflow-coursework-2026"

TASKS=(
    "task1_trends.py"
    "task2_clustering.py"
    "task3_accepted_prediction.py"
    "task4_response_time.py"
    "task5_procrastination.py"
)

# ─── Проверка зависимостей системы ───────────────────────────────────────────
check_requirements() {
    step "Проверка системных зависимостей"

    command -v git  >/dev/null 2>&1 || error "git не установлен"
    command -v python3 >/dev/null 2>&1 || error "python3 не установлен"
    command -v pip  >/dev/null 2>&1 || pip() { python3 -m pip "$@"; }

    local py_version
    py_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    info "Python $py_version"

    # Проверка psql (не обязательно, но полезно)
    if command -v psql >/dev/null 2>&1; then
        success "psql доступен"
    else
        warn "psql не найден — проверка БД будет пропущена"
    fi
}

# ─── Клонирование ────────────────────────────────────────────────────────────
clone_repo() {
    step "Клонирование репозитория"

    if [[ -d "$REPO_DIR" ]]; then
        warn "Директория $REPO_DIR уже существует — пропускаем клонирование"
        info "Для обновления запусти: git -C $REPO_DIR pull"
    else
        git clone "$REPO_URL" "$REPO_DIR"
        success "Репозиторий клонирован"
    fi

    cd "$REPO_DIR"
    success "Рабочая директория: $(pwd)"
}

# ─── Зависимости Python ──────────────────────────────────────────────────────
install_deps() {
    step "Установка Python-зависимостей"

    [[ -f requirements.txt ]] || error "requirements.txt не найден"

    python3 -m pip install --upgrade pip --quiet
    python3 -m pip install -r requirements.txt --quiet
    success "Зависимости установлены"
}

# ─── Настройка .env ──────────────────────────────────────────────────────────
setup_env() {
    step "Настройка окружения (.env)"

    if [[ -f .env ]]; then
        success ".env уже существует — пропускаем"
        return
    fi

    [[ -f .env.example ]] || error ".env.example не найден"
    cp .env.example .env

    echo ""
    warn "Файл .env создан из .env.example"
    echo -e "  Укажи DATABASE_URL своей PostgreSQL БД:"
    echo -e "  ${YELLOW}Пример: postgresql://user:password@localhost:5432/stackoverflow${RESET}"
    echo ""

    # Интерактивный ввод DATABASE_URL
    read -rp "  Введи DATABASE_URL (или Enter для ручного редактирования): " db_url

    if [[ -n "$db_url" ]]; then
        # Заменяем placeholder в .env
        sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=${db_url}|" .env
        rm -f .env.bak
        success "DATABASE_URL сохранён в .env"
    else
        warn "DATABASE_URL не указан — отредактируй .env вручную перед продолжением"
        echo -e "  ${BOLD}nano .env${RESET}  или  ${BOLD}code .env${RESET}"
        read -rp "  Нажми Enter когда .env будет готов..."
    fi
}

# ─── Проверка подключения к БД ───────────────────────────────────────────────
check_db() {
    step "Проверка подключения к БД"

    local db_url
    db_url=$(grep DATABASE_URL .env | cut -d'=' -f2-)

    if [[ -z "$db_url" || "$db_url" == *"your"* || "$db_url" == *"example"* ]]; then
        error "DATABASE_URL в .env не настроен"
    fi

    # Пробуем подключиться через Python
    python3 - <<EOF
import os, sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
try:
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("  Подключение успешно")
except Exception as e:
    print(f"  Ошибка подключения: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    success "БД доступна"
}

# ─── Инициализация схемы ─────────────────────────────────────────────────────
init_schema() {
    step "Создание схемы БД"
    python3 src/storage/loader.py --init
    success "Схема создана"
}

# ─── Загрузка данных ─────────────────────────────────────────────────────────
load_data() {
    step "Загрузка данных CSV → PostgreSQL"

    # Проверяем наличие CSV-файлов
    local csv_count
    csv_count=$(find data/raw -name "*.csv" 2>/dev/null | wc -l)

    if [[ "$csv_count" -eq 0 ]]; then
        warn "CSV-файлы не найдены в data/raw/"
        echo ""
        echo -e "  Скачай данные из Stack Exchange Data Explorer:"
        echo -e "  ${BLUE}https://data.stackexchange.com/stackoverflow/query/new${RESET}"
        echo -e "  SQL-запросы находятся в: ${BOLD}src/sede_queries/${RESET}"
        echo -e "  Сохрани результаты в: ${BOLD}data/raw/${RESET}"
        echo ""
        read -rp "  Нажми Enter когда CSV-файлы будут готовы..."
    fi

    python3 src/storage/loader.py --load
    success "Данные загружены"
}

# ─── Проверка данных ─────────────────────────────────────────────────────────
run_clean() {
    step "Проверка качества данных"
    python3 src/processing/clean.py
    success "Проверка пройдена"
}

# ─── Запуск аналитики ────────────────────────────────────────────────────────
run_analytics() {
    step "Запуск аналитических скриптов"

    mkdir -p notebooks  # Убедимся что папка для графиков существует

    if [[ -n "$SINGLE_TASK" ]]; then
        # Запуск одной задачи
        local idx=$(( SINGLE_TASK - 1 ))
        local task="${TASKS[$idx]:-}"
        [[ -z "$task" ]] && error "Задача $SINGLE_TASK не найдена (допустимо: 1-5)"

        info "Запуск: task${SINGLE_TASK} → $task"
        python3 "src/analytics/$task"
        success "Задача $SINGLE_TASK завершена"
        return
    fi

    # Запуск всех задач
    local total=${#TASKS[@]}
    local failed=()

    for i in "${!TASKS[@]}"; do
        local task="${TASKS[$i]}"
        local num=$(( i + 1 ))

        echo ""
        info "[$num/$total] Запуск: $task"

        if python3 "src/analytics/$task"; then
            success "Задача $num выполнена"
        else
            warn "Задача $num завершилась с ошибкой — продолжаем"
            failed+=("$task")
        fi
    done

    echo ""
    if [[ ${#failed[@]} -eq 0 ]]; then
        success "Все задачи выполнены. Графики сохранены в notebooks/"
    else
        warn "Завершено с ошибками в: ${failed[*]}"
    fi
}

# ─── Итоговый отчёт ──────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}${BOLD}║        Проект успешно запущен        ║${RESET}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "  Графики: ${BOLD}$(pwd)/notebooks/${RESET}"
    echo -e "  Документация: ${BOLD}docs/for_analysts.md${RESET}"
    echo ""
    echo -e "  Запустить одну задачу:"
    echo -e "  ${YELLOW}./setup.sh --only-analytics --task 4${RESET}"
    echo ""
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}"
    echo "  ┌─────────────────────────────────────────┐"
    echo "  │   stackoverflow-coursework-2026 setup   │"
    echo "  └─────────────────────────────────────────┘"
    echo -e "${RESET}"

    check_requirements

    if $ONLY_ANALYTICS; then
        # Только аналитика — предполагаем что мы уже в папке проекта
        [[ -f src/analytics/task1_trends.py ]] || error "Запусти из корня проекта"
        run_analytics
    else
        clone_repo
        install_deps
        setup_env
        check_db
        init_schema
        load_data
        run_clean
        run_analytics
    fi

    print_summary
}

main "$@"
