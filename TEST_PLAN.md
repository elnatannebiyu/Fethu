# Le Gize End-to-End Test Plan

This guide walks you through a full manual test of the Le Gize rental system using the Django admin. It covers logging in as the superadmin, seeding data, verifying CRUD operations, and confirming that role-based guards prevent unauthorized access.

> **Credentials used in this guide**  
> Username: `admin`  
> Password: `12345`

## 1. Prerequisites
1. Activate the virtual environment and run the server:
   ```bash
   cd /Users/elu/Documents/Projects/Fethu/Rental/le_gize
   source .venv/bin/activate
   python manage.py runserver
   ```
2. Open `http://127.0.0.1:8000/admin/` in your browser.
3. Log in with the superadmin credentials above.

## 2. Seed Master Data (Superadmin)
Follow these steps inside the Django admin. After each create action you should return to the listing page and confirm the record appears.

1. **Create Product Category**  
   - Go to **Products → Categories → Add**  
   - Example: `Lighting` with description `Indoor & outdoor lighting equipment`

2. **Create Extra**  
   - **Products → Extras → Add**  
   - Example: `Delivery Service`, price per day `50`

3. **Create Product**  
   - **Products → Products → Add**  
   - Fill fields (category = Lighting, price per day `120`, total stock `20`, available stock `20`, is active = yes).  
   - Pick the `Delivery Service` extra.

4. **Create Customer**  
   - **Orders → Customers → Add**  
   - Example: `Full name: John Doe`, `Phone: 555-0100`

5. **Create Loading Personnel**  
   - Create a regular user first (Accounts → Users → Add) with role `loading`.  
   - Then go to **Personnel → Loading Personnel → Add** and link it to that user.  
   - Fill commission rate (e.g. 10%) and employee ID (e.g. `LP-001`).

## 3. Create & Review an Order
1. **Create Order**  
   - **Orders → Orders → Add**  
   - Select the customer `John Doe`, set order number `ORD-1001`, prepayment 50%, start/end dates, estimated totals as needed.  
   - Save the order.

2. **Add Order Items**  
   - On the order change page, use the **Order items** inline to add the product you created and quantity (e.g. 5).  
   - Add an extra (Delivery Service) with quantity 1 using the **Order extras** inline.

3. **Assign Personnel**  
   - Use the **Personnel allocations** inline to assign `LP-001` at 100%.  
   - Save and confirm the order shows the related entries.

4. **Standalone Section Checks**  
   - Visit **Orders → Order items**, **Orders → Order extras**, and **Orders → Personnel allocations** to confirm the records are visible independently.

## 4. Verify Role-Based Guards
1. **Create Non-Admin User**  
   - Accounts → Users → Add  
   - Username `reception1`, password of your choice, role `reception`, uncheck `is_staff` and `is_superuser`.

2. **Log out** and log back in as `reception1`.

3. **Access Tests**  
   - Try visiting `http://127.0.0.1:8000/admin/` → you should get a “permission denied” page (only staff/superusers can access admin).  
   - Visit the custom front-end dashboard URLs (e.g., `/core/admin-dashboard/`). Because of the mixins in `core/mixins.py`, only admins should see the admin dashboard. Reception users should be redirected with an error message.

4. **Upgrade User to Staff**  
   - Log back in as superadmin.  
   - Edit `reception1` and set `is_staff = True`. Leave `is_superuser = False`.  
   - Log in as `reception1` again and verify that they can enter Django admin but can only see the models they have permission for (no admin-only sections).

## 5. Test Order Workflow as Reception
While logged in as the reception staff user:
1. Create a new customer.  
2. Add an order and confirm you can add order items/extras but cannot change personnel allocations (unless given permission).  
3. Verify the order appears when you log back in as the superadmin.

## 6. Reports & Dashboards (Optional)
- If the custom dashboards are still enabled, log in as admin and visit the following URLs to ensure they load with the new data:  
  - `/core/admin-dashboard/`  
  - `/reports/dashboard/`  
  - `/reports/orders_report/`, `/reports/financial_report/`, etc.

## 7. What to Observe
- **Data persistence**: All records should appear in their respective admin listings.  
- **Permissions**: Only users with the right role/staff status can access restricted views, per `core/mixins.py`.  
- **Integrity**: Products should decrement available stock when tied to orders (if that logic is triggered elsewhere), and personnel allocations should display correct percentages.

Following this script gives you an end-to-end confidence check: admin login, data entry, operational workflow, and permission enforcement.
