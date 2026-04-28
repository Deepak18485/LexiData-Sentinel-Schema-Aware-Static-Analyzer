"""
LexiData-Sentinel Enhanced: Advanced AST Utilities
Supports general DataFrame patterns, multiple variables, dot notation, and method chaining.
"""

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
    - Variables assigned from pd.DataFrame({...}) — with schema inference
    """
    
    def __init__(self):
        self.tracker = DataFrameTracker()
        self.inferred_schemas: Dict[str, Dict[str, dict]] = {}
        self.pandas_methods = {
            'groupby', 'merge', 'join', 'concat', 'pivot', 'pivot_table',
            'melt', 'drop', 'dropna', 'fillna', 'sort_values', 'reset_index',
            'head', 'tail', 'describe', 'info', 'corr', 'value_counts',
            'apply', 'map', 'applymap', 'agg', 'aggregate', 'transform',
            'filter', 'query', 'loc', 'iloc', 'at', 'iat'
        }
    
    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                self.tracker.mark_as_potential(var_name)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if node.attr in self.pandas_methods:
                self.tracker.mark_as_potential(var_name)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """
        Handles: some_var = pd.DataFrame({...})
        Marks it as a DataFrame and infers column schemas from the dict.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                df_name = target.id

                if self._is_pd_dataframe_call(node.value):
                    # Explicitly mark as DataFrame (stronger than potential)
                    self.tracker.mark_as_dataframe(df_name)
                    # Infer schema from the dict argument
                    schema = self._infer_schema_from_dataframe_call(node.value)
                    if schema:
                        self.inferred_schemas[df_name] = schema
                else:
                    # Fallback: if RHS uses a known DataFrame, LHS probably is one too
                    rhs_vars = self._get_variables_in_expr(node.value)
                    for var in rhs_vars:
                        if self.tracker.is_dataframe(var):
                            self.tracker.mark_as_potential(df_name)
                            break

        self.generic_visit(node)

    def _is_pd_dataframe_call(self, node: ast.AST) -> bool:
        """Check if node is pd.DataFrame(...) or pandas.DataFrame(...)"""
        return (
            isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and
            node.func.attr == "DataFrame" and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id in ("pd", "pandas")
        )

    def _infer_schema_from_dataframe_call(self, node: ast.Call) -> Optional[Dict[str, dict]]:
        """
        Extract column names and infer types from pd.DataFrame({"col": [...]}) call.
        Returns: {"col_name": {"type": "int", "nullable": False}, ...}
        """
        if not node.args:
            return None

        dict_node = node.args[0]
        if not isinstance(dict_node, ast.Dict):
            return None

        schema = {}
        for key, value in zip(dict_node.keys, dict_node.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue

            col_name = key.value
            values = []
            nullable = False

            if isinstance(value, ast.List):
                for elt in value.elts:
                    if isinstance(elt, ast.Constant):
                        if elt.value is None:
                            nullable = True
                        else:
                            values.append(elt.value)

            data_type = self._infer_type_from_values(values)
            schema[col_name] = {"type": data_type, "nullable": nullable}

        return schema if schema else None

    def _infer_type_from_values(self, values: list) -> str:
        """
        Infer type string from sample values.
        bool checked before int because bool is a subclass of int in Python.
        """
        for v in values:
            if v is None:
                continue
            if isinstance(v, bool):
                return "bool"
            elif isinstance(v, int):
                return "int"
            elif isinstance(v, float):
                return "float"
            elif isinstance(v, str):
                return "string"
        return "unknown"

    def _get_variables_in_expr(self, node: ast.AST) -> Set[str]:
        """Extract all variable names from an expression."""
        vars_found = set()

        class VarFinder(ast.NodeVisitor):
            def visit_Name(self, n):
                vars_found.add(n.id)

        VarFinder().visit(node)
        return vars_found
def is_dataframe_subscript(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if not isinstance(node.value, ast.Name):
        return False
    var_name = node.value.id
    if df_tracker and not df_tracker.is_dataframe(var_name):
        return False
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return True
    return False


def is_dataframe_attribute(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> bool:
    if not isinstance(node, ast.Attribute):
        return False
    if not isinstance(node.value, ast.Name):
        return False
    var_name = node.value.id
    if df_tracker and not df_tracker.is_dataframe(var_name):
        return False
    method_names = {
        'mean', 'sum', 'min', 'max', 'count', 'std', 'var', 'median',
        'groupby', 'merge', 'join', 'drop', 'fillna', 'dropna', 'head', 'tail',
        'sort_values', 'reset_index', 'set_index', 'describe', 'info', 'shape',
        'columns', 'index', 'values', 'dtypes', 'apply', 'map', 'filter', 'query'
    }
    if node.attr in method_names:
        return False
    if df_tracker and df_tracker.is_dataframe(var_name):
        return True
    return True


def extract_dataframe_reference(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> Optional[DataFrameReference]:
    if isinstance(node, ast.Subscript) and is_dataframe_subscript(node, df_tracker):
        if isinstance(node.value, ast.Name):
            var_name = node.value.id
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                return DataFrameReference(var_name, node.slice.value, "subscript")

    if isinstance(node, ast.Attribute) and is_dataframe_attribute(node, df_tracker):
        if isinstance(node.value, ast.Name):
            return DataFrameReference(node.value.id, node.attr, "attribute")

    return None


def is_assignment_to_column(node: ast.Assign, df_tracker: Optional[DataFrameTracker] = None) -> Tuple[bool, Optional[DataFrameReference]]:
    if len(node.targets) != 1:
        return False, None
    ref = extract_dataframe_reference(node.targets[0], df_tracker)
    if ref:
        return True, ref
    return False, None


def is_aggregation_call(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> Tuple[bool, Optional[str], Optional[DataFrameReference]]:
    if not isinstance(node, ast.Call):
        return False, None, None
    if not isinstance(node.func, ast.Attribute):
        return False, None, None
    func_name = node.func.attr
    aggregation_functions = {"mean", "sum", "min", "max", "count", "std", "var", "median", "quantile", "sem"}
    if func_name in aggregation_functions:
        ref = extract_dataframe_reference(node.func.value, df_tracker)
        if ref:
            return True, func_name, ref
    return False, None, None


def get_binary_op_type(op: ast.operator) -> Optional[str]:
    op_map = {
        ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
        ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**',
    }
    return op_map.get(type(op))


def is_arithmetic_op(op: ast.operator) -> bool:
    return isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow))


def is_comparison_op(op: ast.cmpop) -> bool:
    return isinstance(op, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE))


def extract_all_column_references(node: ast.AST, df_tracker: Optional[DataFrameTracker] = None) -> List[DataFrameReference]:
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

    ReferenceExtractor().visit(node)
    return references


def detect_dataframes_in_code(code: str) -> DataFrameTracker:
    try:
        tree = ast.parse(code)
        detector = DataFrameDetector()
        detector.visit(tree)
        return detector.tracker
    except:
        return DataFrameTracker()