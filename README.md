# Парсер PEP

### Запуск:

**Шаг 1. Клонировать репозиторий:**

```
git@github.com:tWoAlex/bs4_parser_pep.git
```

**Шаг 2. Создать виртуальное окружение и установить необходимые компоненты:**

* Linux:
```
python3 -m venv env
```
```
source env/bin/activate
```
```
pip install -r requirements.txt
```

* Windows:
```
python -m venv venv
```
```
source venv/Scripts/activate
```
```
pip install -r requirements.txt
```

**Шаг 3. Запустить парсер в нужном режиме:**

Перейти в директорию главного файла:
```
cd src
```

Запустить парсер:
```
main.py [-h] [-c] [-o {pretty,file}] {whats-new,latest-versions,download,pep}
```

**Описание флагов:**
1. `-h` справка по парсеру.
2. `-c` очистить кэш.
3. `-o` + `pretty` вывод таблички с информацией в консоль.
4. `-o` + `file` вывод информации в `.csv`-таблицу.

**Описание режимов:**
1. `whats-new` собирает данные со страницы `https://docs.python.org/3/whatsnew/`.
2. `latest-versions` собирает ссылки на документацию последних версий.
3. `download` скачивает архив с PDF-документацией последней версии Python.
4. `pep` считает PEP'ы в каждом статусе.
