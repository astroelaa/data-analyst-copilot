# sales.csv data dictionary

- order_id (int): unique id of the order. Example: 1
- order_date (date): day the order was placed, during 2025. Example: 2025-03-14
- product (text): product name. One of Laptop, Phone, Headphones, Desk, Chair, Notebook, Pen Set, Backpack
- category (text): product category. One of Electronics, Furniture, Stationery, Accessories
- region (text): city of the order. One of Cairo, Alexandria, Giza, Aswan
- quantity (int): units sold in the order, 1 to 5. Example: 3
- unit_price (float): price of one unit in USD. Example: 900.0
- discount (float): discount fraction applied, one of 0, 0.05, 0.1, 0.2
- revenue (float): quantity * unit_price * (1 - discount). Example: 2430.0
