import random
from locust import HttpUser, task, between
import re

# Different user credentials (email-based)
users = [
    {"email": "gpnashik5010@gmail.com", "password": "collegeadmin@1", "role": "admin"},
    {"email": "gpmechanical@gmail.com", "password": "collegemech@1", "role": "department"},
    {"email": "gpddgm@gmail.com", "password": "collegeddgm@1", "role": "department"},
]

class InventoryUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login jab user start hota hai"""
        self.user = random.choice(users)
        # Step 1: GET request to login page
        login_page = self.client.get("/accounts/login/")   # ← Yaha 'login_page' save karo

        # Step 2: CSRF token nikalna from response
        csrftoken = re.search(
            'name="csrfmiddlewaretoken" value="(.+?)"', 
            login_page.text                 # ← login_page.text yaha use karna he
        ).group(1)

        # Step 3: POST request with email, password and csrf token
        login_response = self.client.post(
            "/accounts/login/",
            {
                "email": self.user["email"],
                "password": self.user["password"],
                "csrfmiddlewaretoken": csrftoken,
            },
            headers={"Referer": "http://127.0.0.1:8000/accounts/login/"}
        )

        if login_response.status_code != 200:
            print(f"Login failed for {self.user['email']} (Status {login_response.status_code})")

    @task
    def perform_task(self):
        """Role ke hisaab se tasks"""
        if self.user["role"] == "admin":
            self.admin_tasks()
        else:
            self.department_tasks()

    def admin_tasks(self):
        """Admin user ke liye"""
        self.client.get("/inventory/admin-dashboard")
        self.client.get("/users/manage-users/")
        self.client.get("/inventory/inventory-list/")
        self.client.get("/register/manage-stock-by-register/")
        self.client.get("/stock/allocation")

    def department_tasks(self):
        """Department users ke liye"""
        self.client.get("/inventory/department/inventory/")
