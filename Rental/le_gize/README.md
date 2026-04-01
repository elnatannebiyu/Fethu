# Fethu / Le Gize - Equipment Rental Management System

A Django-based equipment rental platform with multi-role access, inventory management, personnel assignments, and rich reporting.

## 📚 Documentation Map

| Guide | Purpose |
| --- | --- |
| [`SETUP.md`](../../SETUP.md) | Complete environment & installation instructions |
| [`TEST_PLAN.md`](../../TEST_PLAN.md) | Manual end-to-end validation script |
| `tests/scripts/seed_demo_data.py` | Idempotent data seed for demo accounts/orders |

> 🚀 **Quick start**: follow `SETUP.md`, then run `python manage.py shell < tests/scripts/seed_demo_data.py` to load demo data (admin, loader, reception, products, orders).

## 🧩 Key Features

## 📋 User Roles & Features

### 👤 Admin Role
- Access to admin dashboard (`/core/admin-dashboard/`)
- User management and personnel oversight
- Full financial reports (`/reports/financial-report/`)
- Order tracking and analytics
- System configuration

### 🔧 Loading Personnel Role
- Assigned orders dashboard (`/orders/assigned-orders/`)
- Order fulfillment and delivery tracking
- Performance metrics and earnings
- Schedule management

### 🛒 Customer Role
- Browse available products (`/products/product-list/`)
- Place new orders (`/orders/order-page/`)
- View order history and status
- Return requests

## 🏗️ Project Structure

```
le_gize/
├── accounts/          # User authentication, profiles, role management
├── core/             # Core views, dashboards (admin & loading)
├── orders/           # Order management, assignments, returns
├── products/         # Product catalog, categories, extras
├── personnel/        # Loading personnel management, schedules
├── reports/          # Financial and operational reporting
└── templates/        # Django template files (server-side rendered)
```

## 🗄️ Database Schema

- **Custom User Model**: Supports 3 roles (admin, loading, customer)
- **Products**: Equipment catalog with categories and extras
- **Orders**: Active/completed orders with personnel assignments
- **Personnel**: Loading staff profiles, schedules, performance metrics
- **Reports**: Generated financial and operational reports

## 🧪 Testing & Demo Data

- Use `tests/scripts/seed_demo_data.py` to load demo accounts (`admin`, `loader1`, `reception1`), inventory, customer, and order `ORD-1001`.
- Follow `TEST_PLAN.md` for step-by-step manual verification (login with each role, create/inspect orders, confirm permissions).

## 📦 Dependencies

- Django==4.2.7
- python-decouple==3.8
- django-crispy-forms==2.1
- django-filter==23.5
- django-tables2==2.6.0
- whitenoise==6.6.0

## 🛠️ Operations & Commands

Routine commands (migrations, tests, static collection, troubleshooting) are centralized in [`SETUP.md`](../../SETUP.md#quick-reference-commands). Refer there whenever you need the precise shell steps.

## 📝 Notes

- Python 3.10+ is required (project tested on 3.12).
- Static files live in `/static/` (collected to `/staticfiles/`), uploads in `/media/`.
- For detailed setup, maintenance commands, and troubleshooting see [`SETUP.md`](../../SETUP.md); for end-to-end validation use [`TEST_PLAN.md`](../../TEST_PLAN.md).

## 🤝 Support

For issues or questions:
1. Check Python version compatibility first
2. Review the setup commands above
3. Verify all dependencies are installed correctly

---

*Last updated: April 2026*