# Edge Cases and Complex Scenarios
# Tests various corner cases in the analyzer

# Multiple operations on same column
df["score"] = df["balance"] * 2
df["score"] = df["score"] + 100  # Reassigning derived column
final_score = df["score"].mean()

# Nested arithmetic expressions
complex_calc = (df["balance"] + 100) * 1.5 - df["balance"] / 2

# Chained comparisons
age_range = (df["age"] >= 18) and (df["age"] <= 65)

# Multiple aggregations
stats = df["balance"].mean() + df["balance"].std()

# Derived column with mixed types (should infer float)
df["mixed"] = df["balance"] + 10

# Using constants
df["constant_col"] = 42
df["string_col"] = "fixed_value"

# Boolean operations with column access
is_adult = df["age"] > 18
is_premium_adult = df["premium"] and is_adult

# Accessing in different contexts
x = df["name"]  # Read access
comparison = df["name"] == "Alice"  # In comparison
