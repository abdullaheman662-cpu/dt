# FlavorHub – Restaurant Management System

## Project Overview
FlavorHub is a Python desktop application for managing restaurant menu items, customer orders, kitchen order preparation, customer reviews, and sales information. It uses a Tkinter graphical user interface and an SQLite database.

## Main Features
- Dashboard and menu browsing with bundled food images.
- New orders for dine-in, delivery, and self-pickup.
- Shopping cart with quantity management and undo for cart changes.
- Kitchen order queue using FIFO (First In, First Out).
- Smart Allergy Alert to compare selected customer allergies with food allergens.
- Orders, completed orders, and cancelled orders management.
- Customer reviews and sales report.
- Menu management.
- SQLite storage for menu items, orders, order items, and reviews.

## Requirements
- Python 3.10 or newer recommended.
- Tkinter (usually included with standard Python installations).
- SQLite support (included with standard Python).
- Pillow is optional; it can improve display of food images.

## Installation
1. Extract the project ZIP file.
2. Open a terminal or Command Prompt in the extracted project folder (the folder containing `main.py`).
3. Optional: install Pillow for improved image support:
   ```bash
   python -m pip install -r requirements.txt
   ```

## Run the Application
In the folder containing `main.py`, run:

```bash
python main.py
```

On Windows, if `python` is not recognized, use your Python installation's executable path.

## Data Storage
The application creates `flavorhub.db` in the project folder when it runs. This SQLite database stores application data such as menu items, orders, and reviews. Keep this file if you want to retain the saved data.

## Notes
- Keep the `assets` folder beside `main.py`; it contains the food images used by the application.
- Do not move `main.py` away from the `assets` folder or `requirements.txt`.
