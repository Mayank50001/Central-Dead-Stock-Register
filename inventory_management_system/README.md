# 🏫 CDSR - Central Dead Stock Register

The CDSR or the college's inventory management system is tailored for our college's dead stock register's digitization. We have made the long old process of managing the government stock allotment process to colleges into a management software which has all those requirement fulfilled according to the database of the register and all the roles of admin and department and duties of different roles divided in the form of users. Security is enhanced for avoiding unauthorized admin logins and operations in the data.

---

## 📁 Project Structure

```
mayank50001-college_inventory_management_system/
├── inventory_management_system.zip          # Zip file of entire project
└── inventory_management_system/             # Django project folder
    ├── django_db.sql                        # SQL file to pre-load database
    ├── locustfile.py                        # Load testing script using Locust
    ├── manage.py                            # Django entry point
    ├── accounts/                            # User authentication and session tracking
    ├── admin_user_management/               # Admin features to manage department users
    ├── inventory/                           # Core inventory logic and dashboards
    ├── register_management/                 # Handles register-based stock management
    ├── stock_management/                    # Allocation & deallocation of items
    ├── staticfiles/                         # Custom and admin static files (CSS, JS)
    ├── templates/                           # Shared base template
    └── inventory_management_system/         # Project configuration (settings, URLs)
```

---

## ⚙️ Features

- 🔐 Role-based login system (Admin, Department Users)
- 📦 Department Inventory Management
- 📑 Stock Register System with item log tracking
- 📊 Admin Dashboard with user controls and statistics
- 🔁 Item Allocation/Deallocation
- ⏱️ User session timeout via middleware
- 🧪 Load testing support with `locustfile.py`

---

## 🚀 Setup Instructions

### 1. 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

> Make sure MySQL server is running and Python >= 3.8 is installed.

---

### 2. 🛠️ Setup MySQL Database

- Start MySQL server.
- Create a new database:

```sql
CREATE DATABASE inventory_db;
```

- Import the provided SQL file:

```bash
mysql -u root -p inventory_db < django_db.sql
```

---

### 3. ⚙️ Configure `settings.py`

Open `inventory_management_system/settings.py` and set the database config:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'inventory_db',
        'USER': 'your_mysql_username',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost/your ip address',
        'PORT': '3306',
    }
}
```

---

### 4. 📂 Apply Migrations (if needed)

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 5. 👤 Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set up admin login.

---

### 6. 🌐 Run Development Server

```bash
python manage.py runserver
```



## 🧩 App Overview

| App Name               | Description                                        |
|------------------------|----------------------------------------------------|
| `accounts`             | Handles user authentication and activity tracking |
| `admin_user_management`| Admins can add, edit, or remove department users  |
| `inventory`            | Core inventory logic, CRUD, dashboards            |
| `register_management`  | Handles register log of stock flow                |
| `stock_management`     | Item allocation/deallocation                      |

---

## 🧪 Load Testing with Locust (Optional)

Install Locust:

```bash
pip install locust
```

Run:

```bash
locust -f locustfile.py
```

Access Locust Web UI:  
📍 `http://localhost:8089`

---

## 🛠️ Deployment Script (Optional)

A one-shot `setup.sh` script can:
- Install requirements
- Set up virtualenv
- Import DB
- Run server

Let me know if you want this included.

---

## 📝 License

This project is created for academic and educational purposes.
