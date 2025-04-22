# EasyVeggies – Online Vegetable Ordering System
FuelNow is a full-stack web application that allows customers to book fuel
deliveries online and lets administrators manage orders, vegetable types, and users.
---
## Project Overview
This system provides a convenient way for users to:
- Register and log in
- Book different types of vegetables (Carrots, Broccoli)
- Select quantity and delivery schedule
- Track order status
Admins can:
- Add, edit, or delete fuel entries
- Manage vegetable types and stock
- View and manage all orders and users
---
## Tech Stack
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap
- **Tools**: PyCharm, DB Browser, GitHub
---
## Features
### Customer
- Register & Login
- Book vegetables 
- Select delivery time slot
- View past orders
- Cancel orders (if pending)
### Admin
- Dashboard with total stats
- Manage orders (cancel / mark delivered)
- Add/update/delete vegetables
- Manage vegetables types
- View users
---
## Screenshots
| User Booking Page | Admin Dashboard |
|-------------------|------------------|
| ![Booking](uploads/booking.png) | ![Admin](uploads/admin_dashboard.png) |
_(Replace with actual screenshots or links if needed)_
---
## ⛽ How to Run
1. Clone the repository:
```bash
git clone https://github.com/rochas99/easyveggies.git
cd easyveggies
```
2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the app:
```bash
python app.py
```
5. Visit [http://localhost:5000](http://localhost:5000) in your browser.
---
## Folder Structure
```
easyveggies/
├── app.py
├── templates/
│ ├── user/
│ └── admin/
├── models/
├── static/
├── instance/
│ └── db.sqlite
├── requirements.txt
└── README.md
```
---
##  Developed With SDLC
This project followed the **Software Development Life Cycle (SDLC)**:
- Planning
- Requirements Gathering
- Design
- Development
- Testing
- Deployment
- Maintenance
---
##  Author
- **Name**: [Your Name]
- **College/Batch**: [Optional]
- **Date**: [MM/DD/YYYY]
---
##  License
This project is for educational purposes only.
