# Команда 10 · Прикладная статистика

Три исследования на marimo: белое вино, собственные генераторы и UICrit.

## Важные ссылки:

* сайт: https://daisyshrimp-ops.github.io/applied-statistics/
* репозиторий: 


## Обновить GitHub Pages

1. Распакуйте архив и загрузите **всё содержимое** в корень репозитория `daisyshrimp-ops/applied-statistics` с заменой файлов. Одного CSS недостаточно.
2. В GitHub Actions дождитесь зелёного **Deploy site**. Существующий workflow вызывает `python tools/build_site.py`.
3. Обновите страницу Ctrl+F5.

`site/` в архив не включается: Actions собирает его самостоятельно. Эта версия не опубликована автоматически.

## Локальный запуск

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
