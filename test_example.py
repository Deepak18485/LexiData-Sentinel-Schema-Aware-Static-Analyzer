# Enhanced Test File: Multiple DataFrames and Dot Notation
# This demonstrates the analyzer working with various code patterns

# Multiple DataFrame variables
import pandas as pd

# Customers DataFrame
customers = pd.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "David"],
    "age": [25, None, 30, 28],  # nullable for warning case
    "balance": [500.0, 1200.5, 800.75, 1500.0]
})

# Orders DataFrame
orders = pd.DataFrame({
    "amount": [100.0, 250.5, 300.0, 150.75],
    "total": [110.0, 275.5, 330.0, 165.75],
    "date": ["2024-02-01", "2023-12-15", "2024-03-10", "2024-01-20"]
})

# Products DataFrame
products = pd.DataFrame({
    "price": [50.0, 120.0, 75.5, 200.0],
    "category": ["Electronics", "Clothing", "Books", "Furniture"]
})

# Dot notation access
customer_names = customers.name
customer_ages = customers.age
order_amounts = orders.amount

# Subscript notation (also supported)
product_prices = products["price"]
product_categories = products["category"]

# Mixed usage
total_value = customers["balance"] * 1.1
avg_age = customers.age.mean()

# Arithmetic with multiple DataFrames
combined = customers["balance"] + orders["total"]

# Derived columns with dot notation
customers.adjusted_balance = customers.balance * 1.05
orders.discounted = orders.total * 0.9

# Aggregations with dot notation
avg_balance = customers.balance.mean()
total_orders = orders.amount.sum()
max_price = products.price.max()

# Comparisons
high_value_customers = customers.balance > 1000
recent_orders = orders.date > "2024-01-01"
expensive_products = products.price > 100

# This should cause an ERROR - column doesn't exist
invalid = customers.salary.mean()

# This should cause a WARNING - nullable column
risky = customers.age + 10

# This should cause an ERROR - wrong type
bad_math = products.category + 100