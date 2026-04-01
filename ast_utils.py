"""LexiData-Sentinel Enhanced: Advanced AST Utilities
Supports general DataFrame patterns, multiple variables, dot notation, and method chaining."""

import ast
from typing import Optional, Tuple, List, Set, Dict


class DataFrameReference:
    """Represents a reference to a DataFrame column."""
    
    def __init__(self, df_var: str, column: str, access_type: str = "subscript"):
        self.df_var = df_var  # Variable name (e.g., "df", "data", "customers")
        self.column = column  # Column name
        self.access_type = access_type  # "subscript" or "attribute"
    
    def __repr__(self):
        return f"DataFrameReference({self.df_var}['{self.column}'])"
    
    def __eq__(self, other):
        if not isinstance(other, DataFrameReference):
            return False
        return self.df_var == other.df_var and self.column == other.column
    
    def __hash__(self):
        return hash((self.df_var, self.column))


class DataFrameTracker:
    """
    Tracks DataFrame variables throughout the code.
    Identifies which variables are DataFrames through heuristics.
    """
    
    def __init__(self):
        self.dataframe_vars: Set[str] = set()
        self.potential_dataframes: Set[str] = set()
    
    def mark_as_dataframe(self, var_name: str):
        """Explicitly mark a variable as a DataFrame."""
        self.dataframe_vars.add(var_name)
        if var_name in self.potential_dataframes:
            self.potential_dataframes.remove(var_name)
    
    def mark_as_potential(self, var_name: str):
        """Mark a variable as potentially being a DataFrame."""
        if var_name not in self.dataframe_vars:
            self.potential_dataframes.add(var_name)
    
    def is_dataframe(self, var_name: str) -> bool:
        """Check if a variable is known to be a DataFrame."""
        return var_name in self.dataframe_vars or var_name in self.potential_dataframes
    
    def get_all_dataframes(self) -> Set[str]:
        """Get all known DataFrame variables."""
        return self.dataframe_vars | self.potential_dataframes


class DataFrameDetector(ast.NodeVisitor):
    """
    Scans code to identify DataFrame variables using heuristics:
    - Variables used with subscript access: var["column"]
    - Variables used with pandas methods: var.groupby(), var.merge()
    - Variables assigned from pandas operations
    """
    
    def __init__(self):
        self.tracker = DataFrameTracker()
        self.pandas_methods = {
            'groupby', 'merge', 'join', 'concat', 'pivot', 'pivot_table',
            'melt', 'drop', 'dropna', 'fillna', 'sort_values', 'reset_index',
            'head', 'tail', 'describe', 'info', 'corr', 'value_counts',
            'apply', 'map', 'applymap', 'agg', 'aggregate', 'transform',
            'filter', 'query', 'loc', 'iloc', 'at', 'iat'
        }
    
    def visit_Subscript(self, node):
        """Track variables used with subscript notation."""
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            # If it's string subscript, likely a DataFrame
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                self.tracker.mark_as_potential(var_name)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Track variables used with DataFrame-like methods."""
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if node.attr in self.pandas_methods:
                self.tracker.mark_as_potential(var_name)
            # Also check for column access patterns
            # This heuristic: if used in method calls that suggest column operations
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Track pandas function calls that create DataFrames."""
        # Check for pd.read_csv(), pd.DataFrame(), etc.
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in ('pd', 'pandas'):
                    # This is a pandas call, mark result as DataFrame
                    pass
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Track DataFrame assignments."""
        # If RHS involves DataFrames, LHS is also a DataFrame
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Check if RHS involves known DataFrames
                rhs_vars = self._get_variables_in_expr(node.value)
                for var in rhs_vars:
                    if self.tracker.is_dataframe(var):
                        self.tracker.mark_as_potential(target.id)
                        break
        self.generic_visit(node)
    
    def _get_variables_in_expr(self, node: ast.AST) -> Set[str]:
        """Extract all variable names from an expression."""
        vars_found = set()
        
        class VarFinder(ast.NodeVisitor):
            def visit_Name(self, n):
                vars_found.add(n.id)
        
        VarFinder().visit(node)
        return vars_found


def is_dataframe_subscript(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> bool:
    """
    Check if a node represents DataFrame column access via subscript.
    Supports any DataFrame variable name: df["col"], data["col"], etc.
    
    Args:
        node: AST node to check
        df_tracker: Optional tracker of known DataFrame variables
    
    Returns:
        True if node is DataFrame subscript access
    """
    if not isinstance(node, ast.Subscript):
        return False
    
    # Check if the value is a Name node
    if not isinstance(node.value, ast.Name):
        return False
    
    var_name = node.value.id
    
    # If we have a tracker, use it
    if df_tracker and not df_tracker.is_dataframe(var_name):
        return False
    
    # Check if the slice is a string constant (column name)
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return True
    
    return False


def is_dataframe_attribute(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> bool:
    """
    Checking if a node represents DataFrame column access via dot notation.
    Patterns: df.column, data.price, customers.age
    
    Args:
        node: AST node to check
        df_tracker: Optional tracker of known DataFrame variables
    
    Returns:
        True if node is DataFrame attribute access
    """
    if not isinstance(node, ast.Attribute):
        return False
    
    # Check if the value is a Name node (DataFrame variable)
    if not isinstance(node.value, ast.Name):
        return False
    
    var_name = node.value.id
    
    # If we have a tracker, check if it's a known DataFrame
    if df_tracker and not df_tracker.is_dataframe(var_name):
        return False
    
    # Heuristic: if the attribute name doesn't look like a method, it's probably a column
    # Common DataFrame methods to exclude
    method_names = {
        'mean', 'sum', 'min', 'max', 'count', 'std', 'var', 'median',
        'groupby', 'merge', 'join', 'drop', 'fillna', 'dropna', 'head', 'tail',
        'sort_values', 'reset_index', 'set_index', 'describe', 'info', 'shape',
        'columns', 'index', 'values', 'dtypes', 'apply', 'map', 'filter', 'query'
    }
    
    attr_name = node.attr
    
    # If it's a known method, it's not a column
    if attr_name in method_names:
        return False
    
    # If we have a tracker, assume it's a column
    if df_tracker and df_tracker.is_dataframe(var_name):
        return True
    
    # Default: could be a column
    return True


def extract_dataframe_reference(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> Optional[DataFrameReference]:
    """
    Extract DataFrame reference from a node.
    Supports both subscript and attribute access.
    
    Args:
        node: AST node to analyze
        df_tracker: Optional tracker of known DataFrame variables
    
    Returns:
        DataFrameReference if found, None otherwise
    """
    # Subscript: df["column"]
    if isinstance(node, ast.Subscript) and is_dataframe_subscript(node, df_tracker):
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                col_name = node.slice.value
                return DataFrameReference(var_name, col_name, "subscript")
    
    # Attribute: df.column
    if isinstance(node, ast.Attribute) and is_dataframe_attribute(node, df_tracker):
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            col_name = node.attr
            return DataFrameReference(var_name, col_name, "attribute")
    
    return None


def is_assignment_to_column(node: ast.Assign, df_tracker: Optional[DataFrameTracker] = None) -> Tuple[bool, Optional[DataFrameReference]]:
    """
    Check if assignment is creating/modifying a DataFrame column.
    Supports: df["column"] = expr, df.column = expr
    
    Args:
        node: Assignment node
        df_tracker: Optional tracker of DataFrame variables
    
    Returns:
        (is_column_assignment, DataFrameReference)
    """
    if len(node.targets) != 1:
        return False, None
    
    target = node.targets[0]
    ref = extract_dataframe_reference(target, df_tracker)
    
    if ref:
        return True, ref
    
    return False, None


def is_aggregation_call(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> Tuple[bool, Optional[str], Optional[DataFrameReference]]:
    """
    Check if node is an aggregation function call.
    Supports: df["column"].mean(), df.column.sum(), data.price.max()
    
    Args:
        node: AST node to check
        df_tracker: Optional tracker of DataFrame variables
    
    Returns:
        (is_aggregation, function_name, DataFrameReference)
    """
    if not isinstance(node, ast.Call):
        return False, None, None
    
    # Check if it's a method call
    if not isinstance(node.func, ast.Attribute):
        return False, None, None
    
    func_name = node.func.attr
    
    # List of aggregation functions
    aggregation_functions = {"mean", "sum", "min", "max", "count", "std", "var", "median", "quantile", "sem"}
    
    if func_name in aggregation_functions:
        # Check if it's called on a DataFrame column
        ref = extract_dataframe_reference(node.func.value, df_tracker)
        if ref:
            return True, func_name, ref
    
    return False, None, None


def get_binary_op_type(op: ast.operator) -> Optional[str]:
    """Get the string representation of a binary operator."""
    op_map = {
        ast.Add: '+',
        ast.Sub: '-',
        ast.Mult: '*',
        ast.Div: '/',
        ast.FloorDiv: '//',
        ast.Mod: '%',
        ast.Pow: '**',
    }
    return op_map.get(type(op))


def is_arithmetic_op(op: ast.operator) -> bool:
    """Check if operator is arithmetic."""
    return isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow))


def is_comparison_op(op: ast.cmpop) -> bool:
    """Check if operator is comparison."""
    return isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE))


def extract_all_column_references(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> List[DataFrameReference]:
    """
    Recursively extract all DataFrame column references from an expression.
    Supports both subscript and attribute access.
    
    Args:
        node: AST node to analyze
        df_tracker: Optional tracker of DataFrame variables
    
    Returns:
        List of DataFrameReference objects
    """
    references = []
    
    class ReferenceExtractor(ast.NodeVisitor):
        def visit_Subscript(self, sub_node):
            ref = extract_dataframe_reference(sub_node, df_tracker)
            if ref:
                references.append(ref)
            self.generic_visit(sub_node)
        
        def visit_Attribute(self, attr_node):
            ref = extract_dataframe_reference(attr_node, df_tracker)
            if ref:
                references.append(ref)
            self.generic_visit(attr_node)
    
    extractor = ReferenceExtractor()
    extractor.visit(node)
    
    return references


def detect_dataframes_in_code(code: str) -> DataFrameTracker:
    """
    Scan code to automatically detect DataFrame variables.
    
    Args:
        code: Python source code
    
    Returns:
        DataFrameTracker with identified DataFrame variables
    """
    try:
        tree = ast.parse(code)
        detector = DataFrameDetector()
        detector.visit(tree)
        return detector.tracker
    except:
        return DataFrameTracker()