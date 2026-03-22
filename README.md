# LexiData-Sentinel

**A Compiler-Style Static Analysis Tool for Python DataFrame Code**

LexiData-Sentinel performs compile-time semantic analysis on Pandas-style DataFrame operations without executing code or loading data. It uses compiler techniques like AST traversal and symbol tables to detect data-related semantic errors before runtime.

## Overview

This tool treats dataset columns as typed variables and validates operations against a schema, catching errors that would otherwise only appear at runtime (or worse, produce silent incorrect results).

### Key Features

- ✅ **Pure Static Analysis** - No code execution, no Pandas dependency, no data loading
- ✅ **AST-Based** - Uses Python's `ast` module for proper parsing
- ✅ **Schema-Driven** - Column types and nullability defined in JSON metadata
- ✅ **Semantic Validation** - Type checking, nullability analysis, dead code detection
- ✅ **Compiler-Grade Diagnostics** - Errors, warnings, and info messages with line numbers

## Architecture

```
┌─────────────────┐
│  Python Source  │
└────────┬────────┘
         │
         ▼
   ┌──────────┐
   │   AST    │ (Abstract Syntax Tree)
   └────┬─────┘
        │
        ▼
┌───────────────────┐      ┌──────────────┐
│ Semantic Analyzer │◄─────┤ Schema Table │ (Symbol Table)
└────────┬──────────┘      └──────────────┘
         │
         ▼
  ┌────────────┐
  │ Optimizer  │ (Dead Column Detection)
  └──────┬─────┘
         │
         ▼
  ┌─────────────┐
  │ Diagnostics │ (Errors/Warnings/Info)
  └─────────────┘
```

### Module Structure

- **`diagnostics.py`** - Diagnostic collection and reporting system
- **`schema_loader.py`** - Schema parsing and symbol table management
- **`ast_utils.py`** - AST pattern detection utilities
- **`analyzer.py`** - Core semantic analyzer using visitor pattern
- **`optimizer.py`** - Optimization passes (dead column detection)
- **`main.py`** - Pipeline orchestration and CLI

## Usage

### Basic Usage

```bash
python main.py <source_file.py> <schema.json>
```

### With Verbose Output

```bash
python main.py <source_file.py> <schema.json> --verbose
```

### Example

```bash
python main.py test_example.py schema.json
```

## Schema Format

Define your DataFrame schema in JSON:

```json
{
  "columns": [
    {
      "name": "customer_id",
      "type": "int",
      "nullable": false
    },
    {
      "name": "age",
      "type": "int",
      "nullable": true
    },
    {
      "name": "balance",
      "type": "float",
      "nullable": false
    },
    {
      "name": "name",
      "type": "string",
      "nullable": false
    },
    {
      "name": "premium",
      "type": "bool",
      "nullable": false
    }
  ]
}
```

**Supported Types:**
- `int` - Integer numbers
- `float` - Floating-point numbers
- `string` - Text data
- `bool` - Boolean values

## Validation Rules

### Rule Group 1: Column Existence

**ERROR** if a referenced column doesn't exist in the schema.

```python
# Schema has: customer_id, name, age, balance
total = df["salary"].sum()  # ERROR: Column 'salary' not found
```

### Rule Group 2: Type Compatibility

**ERROR** for incompatible type operations.

```python
# ERROR: Cannot perform arithmetic on string
result = df["name"] + df["age"]

# ERROR: Cannot perform arithmetic on bool
calc = df["premium"] * 100
```

### Rule Group 3: Nullability

**WARNING** when nullable columns are used in risky operations.

```python
# age is nullable
risky = df["age"] + 10  # WARNING: Nullable column used in arithmetic
```

### Rule Group 4: Aggregations

**ERROR** for aggregations on non-numeric columns.
**WARNING** for aggregations on nullable columns.

```python
# ERROR: Cannot aggregate string
avg_name = df["name"].mean()

# WARNING: Nullable column aggregation
avg_age = df["age"].mean()  # age is nullable
```

**Supported aggregations:** `mean()`, `sum()`, `min()`, `max()`, `count()`, `std()`, `var()`

### Rule Group 5: Derived Columns

Tracks columns created by assignments and infers their types.

```python
# Creates derived column with inferred float type
df["total_value"] = df["balance"] * 1.1

# Uses derived column
total = df["total_value"].sum()  # OK
```

**INFO** if a derived column is never used after creation.

### Rule Group 6: Dead Columns

**INFO** diagnostics for unused columns:
- Derived columns that are defined but never accessed
- Schema columns that are never accessed in the code

```python
df["temp"] = df["balance"] + 10  # Created
# ... but never used
# INFO: Derived column 'temp' is defined but never used
```

## Example Output

```
======================================================================
LexiData-Sentinel: Static Analyzer for DataFrame Code
======================================================================

[Phase 1] Loading source code...
  ✓ Loaded 1250 characters from test_example.py
[Phase 2] Parsing to Abstract Syntax Tree...
  ✓ Successfully parsed AST
[Phase 3] Loading schema (symbol table)...
  ✓ Loaded schema with 7 column(s)
[Phase 4] Running semantic analysis...
  ✓ Semantic analysis complete
[Phase 5] Running optimization passes...
  ✓ Optimization complete

======================================================================
DIAGNOSTICS
======================================================================

ERROR (line 6): Column 'salary' not found in schema
ERROR (line 10): Invalid arithmetic: cannot use '+' on type string
WARNING (line 10): Nullable column 'age' used in arithmetic operation
ERROR (line 13): Invalid arithmetic: cannot use '*' on type bool
WARNING (line 17): Nullable column 'age' used in arithmetic operation
ERROR (line 21): Cannot apply mean() to non-numeric column 'name' of type string
WARNING (line 24): Aggregation mean() on nullable column 'age' may produce unexpected results
INFO : Derived column 'temp_calc' is defined but never used (defined at line 31)
INFO : Schema column 'customer_id' is never accessed in code

Analysis complete: 4 error(s), 3 warning(s), 2 info(s)

======================================================================
```

## Compiler Concepts Used

This tool demonstrates several compiler techniques:

1. **Lexical Analysis** - Via Python's `ast.parse()`
2. **Syntax Analysis** - AST representation of code structure
3. **Symbol Table** - `SchemaTable` class managing column metadata
4. **Semantic Analysis** - Type checking, nullability validation
5. **Visitor Pattern** - `ast.NodeVisitor` for AST traversal
6. **Type Inference** - Inferring derived column types from expressions
7. **Data Flow Analysis** - Tracking column usage and definitions
8. **Dead Code Elimination** - Detecting unused derived columns
9. **Diagnostic Reporting** - Structured error/warning/info system

## Limitations

- **DataFrame Variable Name** - Currently only recognizes `df` as the DataFrame variable
- **Column Access Pattern** - Only detects `df["column"]` syntax, not `df.column`
- **No Cross-File Analysis** - Analyzes single files independently
- **No Runtime Values** - Cannot validate against actual data values
- **No Control Flow** - Doesn't track conditional branches or loops

## Future Enhancements

Possible extensions:

- **Schema Inference** - Generate draft schemas from code analysis
- **Multiple DataFrames** - Track multiple DataFrame variables
- **Method Chaining** - Better support for `df.method().method()` chains
- **Custom Functions** - Validate user-defined functions
- **Configuration** - Customize which rules to enable/disable
- **IDE Integration** - Language server protocol support
- **pandas API Coverage** - Support more DataFrame operations

## Testing

Run the provided examples:

```bash
# Test file with errors
python main.py test_example.py schema.json

# Valid file (should have minimal issues)
python main.py valid_example.py schema.json

# Verbose mode
python main.py test_example.py schema.json --verbose
```

## Technical Details

### AST Pattern Detection

The tool detects specific AST patterns:

```python
# df["column"] → ast.Subscript node
if isinstance(node, ast.Subscript):
    if isinstance(node.value, ast.Name) and node.value.id == "df":
        if isinstance(node.slice, ast.Constant):
            column_name = node.slice.value

# df["col"].mean() → ast.Call with ast.Attribute
if isinstance(node.func, ast.Attribute):
    if node.func.attr in {"mean", "sum", "min", "max"}:
        # Handle aggregation
```

### Type Inference

Type inference follows these rules:

- `int + int` → `int`
- `int + float` → `float`
- `float + float` → `float`
- Aggregations → `float`
- Unknown operations → `unknown`

### Symbol Table

The `SchemaTable` class maintains:
- Original schema columns
- Derived columns created during execution
- Access counts for each column
- Type and nullability information

