# Enhanced Test File: Multiple DataFrames and Dot Notation
# This demonstrates the analyzer working with various code patterns

# Multiple DataFrame variables
customers = load_data("customers.csv")
orders = load_data("orders.csv")
products = load_data("products.csv")

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