# Users & Roles

Пользователи логинятся встроенными вьюхами Django, а админ через собственную
страницу `/manage/` (не через `/admin/`) смотрит список пользователей и ролей и
назначает или снимает роли.

Пользователь — стандартный `auth.User`, роль — стандартная `auth.Group`,
логин, логаут, хеширование и сессии — из `django.contrib.auth`. Руками написаны
панель, контроль доступа и шаблоны.

## Стек

| Что | Чем |
| --- | --- |
| Язык | Python 3.11+ (собрано на 3.11, CI гоняет 3.12) |
| Фреймворк | Django 5.2 LTS |
| БД | PostgreSQL в docker/CI, SQLite по умолчанию для локалки |
| Frontend | Django templates (SSR) + один файл CSS |
| Аутентификация | `django.contrib.auth`, сессии, встроенные `LoginView` / `LogoutView` |
| Роли | встроенные `auth.Group` |
| Хранилище файлов | `FileSystemStorage` или S3 через django-storages, выбор переменной окружения |
| Конфигурация | `django-environ`, всё из переменных окружения |
| Тесты | pytest + pytest-django, 156 тестов, покрытие 95% |
| Линт | ruff + black, локально через pre-commit |
| E2E | Playwright (chromium), сценарии файлового менеджера |
| CI/CD | GitHub Actions: линтеры → проверки Django → тесты → smoke docker compose → публикация образа в GHCR |

## Быстрый старт

Нужен только Python. БД по умолчанию — SQLite, ставить ничего не надо.

```bash
# 1. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Зависимости
pip install -r requirements-dev.txt   # для прода достаточно requirements.txt

# 3. Настройки: скопировать пример и вписать SECRET_KEY
cp .env.example .env                  # Windows: copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"   # вставить в SECRET_KEY

# 4. База: миграции сразу создают роли admin и user (data-миграция)
python manage.py migrate

# 5. Свой аккаунт администратора
python manage.py createsuperuser

# 6. Тестовые пользователи: админ, обычный, деактивированный и ещё десяток
python manage.py seed_demo_users

# 7. Хуки перед коммитом (ruff, black, проверки Django)
pre-commit install

# 8. Запуск
python manage.py runserver
```

Проверить:

* http://127.0.0.1:8000/login/ — вход;
* http://127.0.0.1:8000/ — «Вы вошли как X, ваши роли: …»;
* http://127.0.0.1:8000/manage/ — панель (только для админов).

Суперпользователь попадает в панель сразу. Чтобы сделать админом обычного
пользователя, добавьте его в группу `admin` — из самой панели или командой:

```bash
python manage.py shell -c "from django.contrib.auth.models import Group, User; User.objects.get(username='ivan').groups.add(Group.objects.get(name='admin'))"
```

## Тестовые пользователи

```bash
python manage.py seed_demo_users              # создать/обновить
python manage.py seed_demo_users --extra 0    # без «массовки» для пагинации
python manage.py seed_demo_users --password 'My-Pass-1' --extra 5
python manage.py seed_demo_users --delete     # удалить всех demo_*
```

Команда идемпотентна: повторный запуск не плодит дубликаты, а возвращает
аккаунты к описанному состоянию (пароль, роли, флаги). При `DEBUG=False` она
отказывается работать без `--force` — чтобы аккаунты с общеизвестным паролем
не уехали в прод.

| Логин | Роль | Зачем нужен |
| --- | --- | --- |
| `demo_admin` | группа `admin` | админ обычным способом, видит `/manage/` |
| `demo_staff` | `is_staff` | проверить второй путь в панель, без группы |
| `demo_user` | группа `user` | обычный юзер, на `/manage/` получает 403 |
| `demo_inactive` | группа `user` | деактивирован, войти не сможет |
| `demo_user01…10` | группа `user` | массовка для поиска и пагинации |

Пароль у всех — `demo-password-123` (меняется флагом `--password`).

## Маршруты

| URL | Что делает | Кто пускается |
| --- | --- | --- |
| `/login/` | вход, встроенная `LoginView` + свой шаблон | все |
| `/logout/` | выход, встроенная `LogoutView` (только POST) | все |
| `/` | домашняя страница: кто вы и какие у вас роли | залогиненные |
| `/files/` | файловый менеджер: список папки, навигация | залогиненные |
| `/files/folder/new/` | создание папки (POST) | залогиненные |
| `/files/upload/` | загрузка файлов (POST) | залогиненные |
| `/files/rename/` | переименование файла или папки | залогиненные |
| `/files/delete/` | удаление с подтверждением | залогиненные |
| `/files/download/` | скачивание файла вложением | залогиненные |
| `/manage/` | список пользователей: поиск, пагинация, роли, активность | админы |
| `/manage/roles/` | список ролей и число участников | админы |
| `/manage/users/<pk>/roles/` | форма назначения/снятия ролей | админы |
| `/manage/users/<pk>/toggle-active/` | включить/выключить пользователя (POST) | админы |
| `/manage/users/new/` | создание пользователя (бонус) | админы |
| `/manage/audit/` | кто кому какую роль менял и когда (бонус) | админы |
| `/admin/` | стандартная админка Django, оставлена как референс | `is_staff` |

Аноним на `/manage/` получает редирект на `/login/?next=…`, залогиненный
не-админ — **403**.

## Переменные окружения

Читаются из `.env` в корне проекта (см. `.env.example`). Реальные переменные
окружения имеют приоритет над файлом, поэтому в CI и docker `.env` не обязателен.

| Переменная | По умолчанию | Зачем |
| --- | --- | --- |
| `SECRET_KEY` | — (обязательна) | ключ Django; без неё проект не стартует |
| `DEBUG` | `False` | режим отладки |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | список через запятую |
| `DATABASE_URL` | `sqlite:///<корень>/db.sqlite3` | например `postgres://user:pass@host:5432/db` |
| `TIME_ZONE` | `UTC` | часовой пояс |
| `STATICFILES_BACKEND` | манифест whitenoise при `DEBUG=False` | чем раздавать статику |
| `SESSION_COOKIE_SECURE` | `False` | включать только на HTTPS |
| `CSRF_COOKIE_SECURE` | `False` | включать только на HTTPS |
| `SECURE_SSL_REDIRECT` | `False` | редирект на HTTPS |
| `SECURE_HSTS_SECONDS` | `0` | HSTS |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | HSTS для поддоменов |
| `SECURE_HSTS_PRELOAD` | `False` | HSTS preload |
| `USE_X_FORWARDED_PROTO` | `False` | доверять `X-Forwarded-Proto` от прокси |
| `LOG_LEVEL` | `INFO` | уровень логов в stdout |
| `FILE_STORAGE_BACKEND` | `local` | `local` — диск сервера, `s3` — бакет AWS |
| `FILE_MANAGER_ROOT` | `<корень>/filemanager` | папка хранилища при `local` |
| `FILE_MANAGER_MAX_FILE_SIZE` | `26214400` | лимит на один файл, байты |
| `FILE_MANAGER_MAX_TOTAL_SIZE` | `536870912` | лимит на всё хранилище, байты |
| `FILE_MANAGER_S3_LOCATION` | `filemanager` | префикс ключей в бакете |
| `AWS_STORAGE_BUCKET_NAME` | пусто | бакет, обязателен при `s3` |
| `AWS_S3_REGION_NAME` | `eu-central-1` | регион бакета |
| `AWS_S3_ENDPOINT_URL` | пусто | адрес S3-эмулятора для локальной проверки |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | пусто | не задаются на EC2: работает IAM-роль |
| `CSRF_TRUSTED_ORIGINS` | пусто | нужно за HTTPS-прокси |

`*_SECURE`-флаги выключены по умолчанию: на локальном HTTP браузер не сохранит
secure-cookie и логин перестанет работать. Перед выкладкой на HTTPS включите их
и проверьте `python manage.py check --deploy`.

## Что взято из коробки, а что написано руками

Из коробки (не переписывалось):

| Возможность | Откуда |
| --- | --- |
| Модель пользователя | `django.contrib.auth.models.User` |
| Роли | `django.contrib.auth.models.Group` |
| Хеширование паролей | `PBKDF2-SHA256`, `set_password` / `check_password` |
| Валидация паролей | `AUTH_PASSWORD_VALIDATORS` |
| Логин и логаут | `auth.views.LoginView`, `auth.views.LogoutView` |
| Форма логина и её сообщения об ошибках | `AuthenticationForm` |
| Сессии | `django.contrib.sessions` |
| CSRF | `CsrfViewMiddleware` + `{% csrf_token %}` |
| Каркас контроля доступа | `LoginRequiredMixin`, `UserPassesTestMixin` |
| Списки, формы, пагинация | `ListView`, `UpdateView`, `CreateView`, `Paginator` |
| Создание пользователя админом | `UserCreationForm` (мы только добавили поля) |
| Миграции, ORM, management-команды | Django |

Написано руками:

| Файл | Что там |
| --- | --- |
| `accounts/permissions.py` | `is_admin()` — единственное определение «кто админ» |
| `accounts/mixins.py` | `AdminRequiredMixin` — контроль доступа для всех вьюх панели |
| `accounts/context_processors.py` | флаг `is_panel_admin` для шаблонов |
| `accounts/views.py` | домашняя страница пользователя |
| `accounts/urls.py` | подключение встроенных `LoginView` / `LogoutView` |
| `accounts/migrations/0001_seed_groups.py` | data-миграция: роли `admin` и `user` |
| `accounts/management/commands/seed_groups.py` | идемпотентный сид ролей |
| `accounts/management/commands/seed_demo_users.py` | тестовые пользователи для локальной проверки |
| `docker/entrypoint.sh` | стартовая последовательность контейнера |
| `panel/views.py` | вьюхи панели `/manage/` |
| `panel/forms.py` | форма ролей и форма создания пользователя |
| `panel/models.py` | `RoleChange` — аудит изменений ролей (бонус) |
| `files/paths.py` | нормализация путей и имён, защита от path traversal |
| `files/storage.py` | контракт хранилища и две реализации: диск и S3 |
| `files/access.py` | правило доступа к разделу файлов |
| `files/views.py` | список, загрузка, переименование, удаление, скачивание |
| `e2e/` | Playwright: сценарии файлового менеджера в браузере |
| `deploy/aws/` | Terraform: бакет, IAM-роль, инстанс |
| `templates/` | все шаблоны, включая `registration/login.html`, 403/404/500 |
| `config/settings.py` | настройки на `django-environ` |
| `config/settings_test.py` | настройки для тестов |
| `.pre-commit-config.yaml` | хуки линтеров перед коммитом |
| `.github/workflows/ci.yml` | пайплайн CI/CD |

## Роли и контроль доступа

Роль — это группа. Сид создаёт две: `admin` и `user`.

Админом считается тот, кто удовлетворяет `accounts.permissions.is_admin`:
состоит в группе `admin`, **или** имеет `is_staff`, **или** суперпользователь.
Это единственное место, где живёт правило; вьюхи, шаблоны и тесты используют его.

Все вьюхи панели наследуются от `AdminRequiredMixin`, копипаста проверок нет:

```python
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return is_admin(self.request.user)
```

Поведение (даётся штатным `AccessMixin`): аноним — редирект на логин с `?next=`,
залогиненный не-админ — `PermissionDenied`, то есть 403. Права проверяются на
каждый запрос, поэтому снятая роль закрывает панель немедленно, без релогина.

## Файловый менеджер

Раздел `/files/`: дерево папок и файлов, создание папок, загрузка нескольких
файлов за раз, переименование, скачивание и удаление с подтверждением.
Хранилище переключается переменной окружения — вьюхи об этом не знают.

**Кому доступен.** Всем залогиненным пользователям: это общий раздел команды, а
не часть админ-панели, поэтому он живёт рядом с `/manage/`, а не внутри неё.
Правило вынесено в `files/access.py` — чтобы отдать файлы только админам,
достаточно поменять там базовый класс на `AdminRequiredMixin`.

### Как устроено хранилище

```
files/storage.py
├── FileManagerStorage   контракт: list_dir, make_dir, save, open, delete,
│                        rename, exists, is_dir, size, total_size
├── LocalFileStorage     поверх FileSystemStorage
└── S3FileStorage        поверх S3Storage из django-storages
```

Backend выбирает `get_storage()` по `FILE_STORAGE_BACKEND`, он же задаёт
`STORAGES["default"]` в настройках — тем же способом, каким `DATABASE_URL`
выбирает базу. Третий backend добавляется новым подклассом: вьюхи и шаблоны
не меняются.

Папки в S3 виртуальные: пустая папка — это объект нулевого размера с ключом,
оканчивающимся на `/`. Удаление папки удаляет все ключи с её префиксом,
переименование копирует их на новый префикс и удаляет старые.

### Режим S3

```bash
# в .env
FILE_STORAGE_BACKEND=s3
AWS_STORAGE_BUCKET_NAME=имя-бакета
AWS_S3_REGION_NAME=eu-central-1
```

Ключи задавать не нужно, если приложение работает на EC2 с IAM-ролью — boto3
возьмёт временные креды из метаданных инстанса. Локально проверить S3-режим без
облака можно на localstack:

```bash
docker compose --profile s3 up --build
# в .env дополнительно: AWS_S3_ENDPOINT_URL=http://localstack:4566
```

### Безопасность

| Что | Как закрыто |
| --- | --- |
| Path traversal | `files/paths.py`: `..`, абсолютные пути, диски и null-байты отбиваются до обращения к хранилищу, ответ — 400 |
| Симлинк наружу | локальное хранилище дополнительно сверяет уже разрешённый путь с корнем |
| Имена файлов | запрещены разделители, управляющие символы, зарезервированные windows-имена, длина ограничена 120 символами |
| Размер | лимит на файл и на суммарный объём хранилища, оба из переменных окружения |
| Опасные расширения | скачивание всегда идёт с `Content-Disposition: attachment`, плюс `X-Content-Type-Options: nosniff` — браузер не выполнит `.html` или `.svg` |
| Перезапись | файл с существующим именем не перезаписывается молча, а даёт ошибку |
| Секреты | ключи AWS только в `.env` и в IAM-роли, в репозитории их нет |

Все пункты закрыты тестами: `tests/test_files_paths.py`,
`tests/test_files_storage.py`, `tests/test_files_views.py`.

## Тесты

```bash
pytest                                  # 156 тестов
pytest -v
pytest --cov --cov-report=term-missing  # покрытие (сейчас 95%)
```

Тесты используют `config/settings_test.py`: свой `SECRET_KEY`, статика без
манифеста и быстрый хешер паролей. Поэтому `pytest` работает на свежем клоне,
без `.env` и без `collectstatic`. Боевой хешер проверяется отдельным тестом,
который включает `PBKDF2PasswordHasher` явно.

Покрыто:

* `tests/test_auth.py` — вход успешный и неуспешный, отсутствие утечки
  «существует ли такой юзер», неактивный пользователь, логаут, редирект
  неавторизованного, **пароль в `auth_user` лежит хешем** (читается прямым SQL);
* `tests/test_access_control.py` — аноним → редирект, обычный юзер → 403,
  группа `admin` / `is_staff` / суперюзер → 200, снятие роли закрывает доступ;
* `tests/test_roles.py` — назначение и снятие роли меняют БД, пишется аудит,
  чужому доступ закрыт, POST без CSRF-токена отбивается;
* `tests/test_panel.py` — поиск, пагинация, активация/деактивация, создание
  пользователя, страница аудита;
* `tests/test_seed_groups.py` — роли появляются после `migrate`, команда
  `seed_groups` идемпотентна;
* `tests/test_seed_demo_users.py` — тестовые юзеры создаются с нужными ролями и
  флагами, команда идемпотентна, `--delete` не трогает чужие аккаунты, при
  `DEBUG=False` без `--force` команда отказывается работать;
* `tests/test_files_paths.py` — path traversal во всех видах, санитизация имён;
* `tests/test_files_storage.py` — **контракт хранилища, прогнанный дважды**: для
  локального диска и для S3 через `moto`. Один и тот же набор проверок, разные
  реализации;
* `tests/test_files_views.py` — доступ анонима, лимиты размера, вложение при
  скачивании, рекурсивное удаление, 400 на путь наружу.

Тестовое окружение задаётся в корневом `conftest.py` (там же `SECRET_KEY` для CI),
фикстуры пользователей — в `tests/conftest.py`.

## E2E-тесты (Playwright)

Pytest проверяет бэкенд и вьюхи, Playwright — что сценарий работает в реальном
браузере. Одно другое не заменяет.

```bash
cd e2e
npm ci
npx playwright install chromium
BASE_URL=http://127.0.0.1:8000 npx playwright test      # против поднятого стека
npx playwright show-report                              # отчёт после прогона
```

Приложение для тестов поднимается тем же `docker compose`, что и обычно.
Пользователь берётся из `seed_demo_users` — `demo_admin` с паролем из README,
переопределяется через `E2E_USERNAME` / `E2E_PASSWORD`.

```
e2e/
├── playwright.config.ts   baseURL из окружения, retries только в CI,
│                          trace on-first-retry, видео и скриншот при падении
├── support/
│   ├── fixtures.ts        логин, уникальные имена, фикстура workspace
│   └── file-manager.page.ts   Page Object раздела
├── auth.spec.ts           доступ анонима, вход, переход в раздел
├── folders.spec.ts        создание, вложенность, крошки, дубликат, удаление
└── files.spec.ts          загрузка (одного и нескольких), переименование,
                           скачивание, удаление, файл больше лимита
```

Каждый тест работает в своей папке с уникальным именем и убирает её за собой —
прогоны не зависят друг от друга и от порядка. Ожиданий по таймеру нет: только
web-first assertions, которые сами дожидаются нужного состояния.

**Про codegen.** Черновики сценариев снимались через `npx playwright codegen`,
дальше приводились в порядок руками: локаторы заменены на `getByRole`,
`getByLabel` и `getByTestId`, повторяющиеся шаги вынесены в Page Object и
фикстуры, шаги подписаны через `test.step()`. Для устойчивых локаторов в
шаблоны точечно добавлены `aria-label`, `role="status"` и `data-testid` — это
честнее, чем цепляться за классы вёрстки.

## Линт и форматирование

```bash
ruff check .            # проверить
ruff check --fix .      # починить автоматом
black .                 # отформатировать
black --check .         # только проверить, как в CI
```

Локально всё это удобнее гонять через pre-commit — он же стоит хуком на коммит:

```bash
pre-commit install          # один раз после клонирования
pre-commit run --all-files  # прогнать по всему репозиторию
pre-commit autoupdate       # обновить версии хуков
```

Хуки: базовая гигиена файлов (конец строки, пробелы, крупные файлы, приватные
ключи, валидность YAML/TOML), `ruff --fix`, `black`, плюс два локальных —
`manage.py check` и `makemigrations --check` (ловит забытые миграции).
Локальные хуки зовут `python` из PATH, поэтому коммитить нужно с активированным
venv.

## CI/CD

`.github/workflows/ci.yml` — на каждый push в `main`, на каждый pull request и
по кнопке (`workflow_dispatch`). Пять job-ов:

| Job | Что делает |
| --- | --- |
| **Линтеры** | `ruff check`, `black --check`, полный прогон `pre-commit` |
| **Проверки Django** | `manage.py check`, `makemigrations --check` (забытые миграции), `check --deploy --fail-level WARNING` с включёнными HTTPS-флагами |
| **Тесты** | матрица Python 3.12 и 3.13, реальный PostgreSQL 16 в сервис-контейнере, `pytest --cov --cov-fail-under=90`, отчёт о покрытии в артефактах |
| **docker compose up** | поднимает стек как в проде, проверяет 302 для анонима на `/manage/` и `/files/`, вход админом и что роли засеяны |
| **E2E (Playwright)** | поднимает тот же стек, ставит chromium, гоняет сценарии файлового менеджера, при падении сохраняет отчёт Playwright артефактом |
| **Публикация в GHCR** | ждёт зелёных smoke и E2E; только для `main` и тегов `v*`: собирает образ и пушит в `ghcr.io/<owner>/<repo>` с тегами `latest`, `sha-…`, semver. Использует встроенный `GITHUB_TOKEN`, секреты настраивать не нужно |

CD доведён до публикации образа: дальше на своём сервере достаточно
`docker compose pull && docker compose up -d` с этим образом. Обновление
зависимостей — `.github/dependabot.yml` (pip, GitHub Actions, Docker, раз в неделю).

## PostgreSQL вместо SQLite

Достаточно поменять одну переменную в `.env`:

```
DATABASE_URL=postgres://users_roles:users_roles@localhost:5432/users_roles
```

Драйвер `psycopg[binary]` уже в `requirements.txt`, дальше обычный
`python manage.py migrate`.

## Docker

```bash
cp .env.example .env     # SECRET_KEY обязателен, остальное compose перекроет
docker compose up --build
```

Поднимутся Postgres и приложение на http://127.0.0.1:8000/. Всё, что нужно для
старта, делает `docker/entrypoint.sh`:

1. `migrate` — схема и роли `admin` / `user` (их создаёт data-миграция);
2. `seed_groups` — на случай, если роль удалили руками;
3. `seed_demo_users` — **только если** `SEED_DEMO_USERS=1`;
4. `collectstatic` — статика для whitenoise;
5. `exec` на команду из `CMD`, то есть gunicorn.

В `docker-compose.yml` флаг включён, поэтому сразу после `up` можно войти как
`demo_admin` / `demo-password-123`. Для боевого запуска уберите переменную или
поставьте `"0"` — в самом образе сид по умолчанию выключен, аккаунты с известным
паролем в бою не нужны.

```bash
docker compose exec web python manage.py createsuperuser   # свой аккаунт
docker compose logs -f web                                 # логи, включая шаги старта
```

Статика собирается на этапе сборки образа, зависимости ставятся из
`requirements.lock` (генерируется `pip-compile requirements.txt`), процесс внутри
контейнера работает от непривилегированного пользователя `app`.

`migrate` в entrypoint рассчитан на один инстанс — при нескольких репликах они
будут стартовать одновременно и гонки за миграции никто не разруливает. Это
осознанное упрощение: в проде миграции гоняют отдельным шагом деплоя.

### Что происходит с данными

База лежит в именованном томе `pgdata`, а не внутри контейнера, поэтому:

| Команда | Что с данными |
| --- | --- |
| `docker compose stop` / `restart` | сохраняются |
| `docker compose down` | сохраняются (удаляются только контейнеры) |
| `docker compose up` после выключения компьютера | сохраняются |
| `docker compose down -v` | **удаляются вместе с томом** |

То есть пропасть данные могут только от явного `-v`. При следующем старте
entrypoint снова прогонит миграции и сид — на пустой базе получится чистый
стенд, на существующей ничего не сломается: обе команды идемпотентны.

## Деплой в AWS

Разворачивается всё приложение целиком — `/manage/`, `/files/` и остальное, —
а не файловый менеджер отдельно.

### Что поднимается

| Сервис | Зачем |
| --- | --- |
| S3 | хранилище файлового менеджера, приватный бакет с шифрованием и блокировкой публичного доступа |
| EC2 (t3.micro, free tier) | инстанс с Docker; тянет образ из GHCR и поднимает его вместе с Postgres |
| IAM-роль инстанса | доступ к бакету **только** на `ListBucket`, `GetObject`, `PutObject`, `DeleteObject` — без ключей в коде и без `AdministratorAccess` |
| Security group | наружу открыт только 80-й порт; SSH — лишь если явно указать свой адрес |

```
браузер → EC2 (:80 → gunicorn:8000) ─┬→ Postgres в контейнере на том же инстансе
                                     └→ S3 (файлы), доступ по IAM-роли, IMDSv2
```

### Живой стенд

Развёрнут и проверен: приложение работает, файлы уезжают в S3.

| | |
| --- | --- |
| Адрес | http://100.54.108.163/ |
| Учётка для просмотра | `demo_admin` / `demo-password-123` |
| Регион | `us-east-1` |
| Бакет | `users-and-roles-files-f92fa1c9` |
| Образ | `ghcr.io/senpai520120/django_application:0.2.0` |

Стенд временный и будет погашен после проверки — команда сноса ниже.

### Шаги

```bash
cd deploy/aws
terraform init
terraform apply   -var region=us-east-1   -var bucket_name=имя-бакета-глобально-уникальное   -var key_name=имя-вашей-ключевой-пары   -var ssh_cidr=ваш.ip.адрес/32   -var image=ghcr.io/senpai520120/django_application:0.2.0
```

Ключевая пара привязана к региону: разворачивайте туда же, где она создана.
Файл `terraform.tfstate` содержит сгенерированные `SECRET_KEY` и пароль базы —
он в `.gitignore`, коммитить и пересылать его нельзя.

Terraform выведет `app_url` — по нему приложение и открывается. Первый старт
занимает пару минут: инстанс ставит Docker и тянет образ. `SECRET_KEY` и пароль
базы генерируются самим Terraform и попадают только в `.env` на инстансе.

Приложение стартует с `FILE_STORAGE_BACKEND=s3`, поэтому загруженные файлы
сразу уезжают в бакет. Проверить: загрузите файл в `/files/` и посмотрите
`aws s3 ls s3://имя-бакета/filemanager/`.

Если разворачиваете без Terraform, IAM-политика минимальных прав лежит в
`deploy/aws/iam-policy.json` — подставьте туда имя бакета.

### Как снести всё после проверки

```bash
cd deploy/aws
terraform destroy   -var region=us-east-1   -var bucket_name=users-and-roles-files-f92fa1c9   -var key_name=test_django
```

Одна команда убирает инстанс, бакет вместе с файлами (`force_destroy = true`),
IAM-роль, политику и security group. Ручная проверка, что ничего не капает:

- [ ] EC2 → Instances: инстанс `users-and-roles-app` в состоянии terminated;
- [ ] S3 → бакета в списке нет;
- [ ] IAM → Roles: роли `users-and-roles-app` нет;
- [ ] EC2 → Security Groups: группы `users-and-roles-app` нет;
- [ ] EC2 → Elastic IPs: нет висящих адресов (Terraform их не создаёт, но если
      выдавали руками — освободите, они платные в простое);
- [ ] Billing → Cost Explorer через сутки: по проекту ноль.

## Проверить, что пароли захешированы

```bash
# SQLite
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.values_list('username', 'password')[:5])"

# PostgreSQL
psql "$DATABASE_URL" -c "select username, password from auth_user limit 5;"
```

В колонке `password` должно быть что-то вида
`pbkdf2_sha256$1000000$<соль>$<хеш>`. Это же проверяет тест
`tests/test_auth.py::test_password_is_stored_hashed`.

## Структура

```
config/           настройки, корневой urls.py, wsgi/asgi
accounts/         аутентификация, домашняя страница, правила доступа, сид ролей
  permissions.py    is_admin() и имена ролей
  mixins.py         AdminRequiredMixin
  migrations/       data-миграция с ролями admin и user
  management/       команда seed_groups
panel/            кастомная админка на /manage/
  views.py          списки, форма ролей, создание юзера, аудит
  forms.py          формы поверх встроенных
  models.py         RoleChange (аудит-лог)
files/            файловый менеджер на /files/
  paths.py          нормализация путей, защита от traversal
  storage.py        контракт хранилища + local и s3
  access.py         кто пускается в раздел
  views.py          список, загрузка, переименование, удаление, скачивание
e2e/              Playwright: сценарии в браузере
deploy/aws/       Terraform: S3, IAM-роль, EC2
templates/        base.html, registration/login.html, панель, 403/404/500
static/css/       единственный css-файл
tests/            pytest-django
```

## Известные ограничения

* Аудит покрывает только изменение ролей. Создание пользователя и
  активация/деактивация в `RoleChange` не пишутся: модель заточена под роли.
  Чтобы логировать всё, её нужно обобщить до `AuditEntry` с полем `action`.
* Нет защиты от перебора паролей. Форма логина не ограничивает попытки — в
  боевом проекте сюда ставят `django-axes` или rate limit на уровне nginx.
* `is_admin()` считает админом и участника группы `admin`, и любого `is_staff`.
  Снять `is_staff` через панель нельзя — только через `/admin/` или shell;
  в списке пользователей такие флаги видны отдельной колонкой.

## Что не делалось

Вне scope задачи:

* регистрация пользователей через публичный UI — аккаунты заводит админ или
  `createsuperuser`;
* восстановление пароля, подтверждение email, OAuth/SSO;
* REST API, SPA, JS-фреймворки;
* отдельная модель `Role` — роль это `auth.Group`, дублировать её незачем
  (описание роли понадобится — заведём `Role` с `OneToOne` на `Group`).

Стандартный `/admin/` включён, но задача решена своей страницей `/manage/`.
