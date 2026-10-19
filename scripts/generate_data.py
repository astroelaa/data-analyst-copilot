import numpy as np
import pandas as pd


rng = np.random.default_rng(42)
products = {
    "Laptop": ("Electronics", 900),
    "Phone": ("Electronics", 600),
    "Headphones": ("Electronics", 80),
    "Desk": ("Furniture", 250),
    "Chair": ("Furniture", 150),
    "Notebook": ("Stationery", 5),
    "Pen Set": ("Stationery", 12),
    "Backpack": ("Accessories", 45),
}
regions = ["Cairo", "Alexandria", "Giza", "Aswan"]
product_names = list(products)
order_days = pd.date_range("2025-01-01", "2025-12-31", freq="D")

selected_products = rng.choice(product_names, size=2000)
quantities = rng.integers(1, 6, size=2000)
discounts = rng.choice([0, 0.05, 0.1, 0.2], size=2000)
data = pd.DataFrame(
    {
        "order_id": np.arange(1, 2001),
        "order_date": rng.choice(order_days, size=2000),
        "product": selected_products,
        "category": [products[product][0] for product in selected_products],
        "region": rng.choice(regions, size=2000),
        "quantity": quantities,
        "unit_price": [products[product][1] for product in selected_products],
        "discount": discounts,
    }
)
data["revenue"] = (
    data["quantity"] * data["unit_price"] * (1 - data["discount"])
).round(2)
data = data.sort_values("order_date").reset_index(drop=True)
data.to_csv("data/sales.csv", index=False)
