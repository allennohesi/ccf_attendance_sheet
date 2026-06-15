# CCF Attendance

Production-ready Django attendance system for CCF activities with custom users, role management, activity management, and QR-based attendance scanning.

## Features

- Custom email-auth user model with profile fields, role assignment, and UUID-based QR code.
- Multi-role user assignment (admin can add/remove several roles per user).
- Includes an `ADMIN` role that has top-level management access in the app.
- Public registration + login, plus admin-controlled role management.
- Activity CRUD with attendance list and CSV export.
- QR scanning page using `html5-qrcode` and AJAX attendance recording.
- Duplicate attendance prevention (`user + activity` unique constraint).
- Admin dashboard analytics (attendance totals and top activities).

## Tech Stack

- Django 5.1 (LTS family)
- Django REST Framework (installed for API extension)
- SQLite for local development, PostgreSQL-ready settings via env vars
- Bootstrap 5 UI
- `qrcode` + `Pillow` for QR image generation
- Dynamic `Role` model + true many-to-many user↔role membership (join table `accounts_user_role_memberships`, **not** stored in `account_user` rows)

## Run Locally

1. Install dependencies:

   ```bash
   python -m pip install django djangorestframework qrcode pillow
   ```

2. Run migrations:

   ```bash
   python manage.py migrate
   ```

3. Create superuser:

   ```bash
   python manage.py createsuperuser
   ```

4. Start dev server:

   ```bash
   python manage.py runserver
   ```

5. Open:
   - App: `http://127.0.0.1:8000/`
   - Django admin: `http://127.0.0.1:8000/admin/`

## Environment Variables (Optional)

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`True`/`False`)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DB_ENGINE` (e.g. `django.db.backends.postgresql`)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
# ccf_attendance_sheet
