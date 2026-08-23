# Users & Roles

Django-приложение: пользователи логинятся встроенными вьюхами Django, а админ
через **собственную** страницу `/manage/` (не через `/admin/`) смотрит список
пользователей и ролей и назначает/снимает роли.

Главный принцип проекта: **не переписывать то, что Django даёт из коробки**.
Пользователь — стандартный `django.contrib.auth.models.User`, роль — стандартная
`django.contrib.auth.models.Group`, логин/логаут/хеширование/сессии — из
`django.contrib.auth`. Руками написаны только панель, контроль доступа и шаблоны.

## Стек

| Что | Чем |
| --- | --- |
| Язык | Python 3.11+ (собрано на 3.11, CI гоняет 3.12) |
| Фреймворк | Django 5.2 LTS |
| БД | PostgreSQL в docker/CI, SQLite по умолчанию для локалки |
| Frontend | Django templates (SSR) + один файл CSS |
| Аутентификация | `django.contrib.auth`, сессии, встроенные `LoginView` / `LogoutView` |
| Роли | встроенные `auth.Group` |
| Конфигурация | `django-environ`, всё из переменных окружения |
| Тесты | pytest + pytest-django, 43 теста, покрытие 98% |
| Линт | ruff + black, локально через pre-commit |
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

# 8. Поехали
python manage.py runserver
```

Дальше:

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
| `CSRF_TRUSTED_ORIGINS` | пусто | нужно за HTTPS-прокси |

`*_SECURE`-флаги по умолчанию выключены намеренно: на локальном HTTP браузер
не сохранит secure-cookie и логин просто перестанет работать. Перед выкладкой
на HTTPS включите их и проверьте `python manage.py check --deploy`.

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
| `panel/views.py` | вьюхи панели `/manage/` |
| `panel/forms.py` | форма ролей и форма создания пользователя |
| `panel/models.py` | `RoleChange` — аудит изменений ролей (бонус) |
| `templates/` | все шаблоны, включая `registration/login.html`, 403/404/500 |
| `config/settings.py` | настройки на `django-environ` |
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

## Тесты

```bash
pytest                                  # 43 теста
pytest -v
pytest --cov --cov-report=term-missing  # покрытие (сейчас 98%)
```

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
  `DEBUG=False` без `--force` команда отказывается работать.

Тестовое окружение задаётся в корневом `conftest.py` (там же `SECRET_KEY` для CI),
фикстуры пользователей — в `tests/conftest.py`.

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
| **docker compose up** | поднимает стек как в проде, ждёт ответа приложения, проверяет 302 для анонима на `/manage/` и что роли засеяны, гасит стек |
| **Публикация в GHCR** | только для `main` и тегов `v*`: собирает образ и пушит в `ghcr.io/<owner>/<repo>` с тегами `latest`, `sha-…`, semver. Использует встроенный `GITHUB_TOKEN`, секреты настраивать не нужно |

CD доведён до публикации образа: дальше на своём сервере достаточно
`docker compose pull && docker compose up -d` с этим образом. Обновление
зависимостей — `.github/dependabot.yml` (pip, GitHub Actions, Docker, раз в неделю).

## PostgreSQL вместо SQLite

Достаточно поменять одну переменную в `.env`:

```
DATABASE_URL=postgres://users_roles:users_roles@localhost:5432/users_roles
```

Драйвер (`psycopg[binary]`) уже в `requirements.txt`. Дальше как обычно:
`python manage.py migrate`.

## Docker

```bash
cp .env.example .env     # SECRET_KEY обязателен, остальное compose перекроет
docker compose up --build
```

Поднимутся Postgres и приложение на http://127.0.0.1:8000/. Контейнер сам
прогоняет `migrate`, `seed_groups` и `collectstatic`, статику раздаёт whitenoise,
сервер — gunicorn. Суперпользователя создать так:

```bash
docker compose exec web python manage.py createsuperuser
```

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
templates/        base.html, registration/login.html, панель, 403/404/500
static/css/       единственный css-файл
tests/            pytest-django
```

## Границы задачи

Сознательно не делалось (вне scope):

* регистрация пользователей через публичный UI — аккаунты заводит админ или
  `createsuperuser`;
* восстановление пароля, подтверждение email, OAuth/SSO;
* REST API, SPA, JS-фреймворки;
* отдельная модель `Role` — роль это `auth.Group`, дублировать её незачем
  (описание роли понадобится — заведём `Role` с `OneToOne` на `Group`).

Стандартный `/admin/` включён, но задача решена своей страницей `/manage/`.
#   d j a n g o _ a p p l i c a t i o n 
 
 
