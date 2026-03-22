# Valid example with no errors
# This demonstrates correct usage of DataFrame operations

# Calculate adjusted balance for all customers
df["adjusted_balance"] = df["balance"] * 1.05

# Filter young premium customers
young_premium = df["age"] < 35
is_premium = df["premium"] == True
qualified_customers = young_premium and is_premium

# Calculate statistics on balance
total_balance = df["balance"].sum()
avg_balance = df["balance"].mean()
max_balance = df["balance"].max()

# Create derived metrics
df["balance_category"] = df["region"]
df["customer_value"] = df["adjusted_balance"] + 100.0

# Use derived columns
high_value = df["customer_value"] > 1000
final_report = df["customer_value"].mean()

# Access all required columns
customer_name = df["name"]
customer_id = df["customer_id"]
customer_discount = df["discount"]
