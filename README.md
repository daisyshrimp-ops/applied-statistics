# Команда 10 · Прикладная статистика

Три исследования на marimo: белое вино, собственные генераторы и UICrit.

## Важные ссылки:

* сайт: https://daisyshrimp-ops.github.io/applied-statistics/
* репозиторий: https://github.com/daisyshrimp-ops/applied-statistics
* файлы с jupiter notebook лежат в папке research, открывать только sprint1.ipynb(1 спринт),sprint2.ipynb(второй спринт - генератор), uicrit.ipynb(доп ктвд), остальное не надо :( и рекомендуется смотреть в колабе, по крайней мере доп часть ктвд!!
* также исходные ноутбуки можно найти в футере сайта, к каждой вкладке прикреплено свое исследование



## Локальный запуск(пусть будет тоже тут)

На Windows запустите `START_WINDOWS.bat`: он установит зависимости, соберёт актуальный `lab01.py` и откроет marimo.

Ручной запуск из каталога проекта:

```bash
python -m pip install -r requirements.txt
python tools/compose_site.py
python -m marimo run lab01.py
```

Для пересборки исходных выводов и HTML/WASM:

```bash
python tools/build_site.py
```
