"""
LexiData-Sentinel Enhanced: Advanced Semantic Analyzer
Supports multiple DataFrames, dot notation, method chaining, and general code patterns.
"""

import ast
from typing import Optional, Dict, Set

from diagnostics import DiagnosticCollector
from schema_base import DataType, ColumnSymbol
from schema_loader import MultiDataFrameSchema
from ast_utils import (
    DataFrameTracker,
    DataFrameReference,
    extract_dataframe_reference,
    is_assignment_to_column,
    is_aggregation_call,
    get_binary_op_type,
    is_arithmetic_op,
    extract_all_column_references,
    detect_dataframes_in_code
)


class EnhancedSemanticAnalyzer(ast.NodeVisitor):
    """
    Enhanced semantic analyzer supporting:
    - Multiple DataFrame variables
    - Both subscript (df["col"]) and attribute (df.col) access
    - Method chaining
    - Function definitions
    - Control flow (basic)
    """
    
    def __init__(
        self,
        schema: MultiDataFrameSchema,
        diagnostics: DiagnosticCollector,
        df_tracker: Optional[DataFrameTracker] = None
    ):
        self.schema = schema
        self.diagnostics = diagnostics
        self.df_tracker = df_tracker or DataFrameTracker()
        self.current_line: Optional[int] = None
        
        # Track function scopes
        self.in_function = False
        self.function_depth = 0
    
    def analyze(self, tree: ast.AST):
        """Entry point for semantic analysis."""
        self.visit(tree)
    
    def visit(self, node):
        """Override visit to track current line number."""
        if hasattr(node, 'lineno'):
            self.current_line = node.lineno
        return super().visit(node)
    
    # === DataFrame Variable Tracking ===
    
    def _ensure_dataframe_tracked(self, df_name: str):
        """Ensure a DataFrame variable is tracked."""
        if not self.df_tracker.is_dataframe(df_name):
            self.df_tracker.mark_as_potential(df_name)
    
    # === RULE GROUP 1: Column Existence ===
    
    def check_column_exists(
        self,
        ref: DataFrameReference,
        line: Optional[int] = None
    ) -> bool:
        """
        Verify that a column exists in the schema for a specific DataFrame.
        Reports ERROR if column is not found.
        """
        if not self.schema.column_exists(ref.df_var, ref.column):
            self.diagnostics.error(
                f"Column '{ref.column}' not found in DataFrame '{ref.df_var}'",
                line or self.current_line
            )
            return False
        return True
    
    def visit_Subscript(self, node: ast.Subscript):
        """Handle df["column"] access."""
        ref = extract_dataframe_reference(node, self.df_tracker)
        if ref:
            # Ensure DataFrame is tracked
            self._ensure_dataframe_tracked(ref.df_var)
            
            # Check if column exists
            if self.check_column_exists(ref, node.lineno):
                # Mark as accessed
                self.schema.mark_accessed(ref.df_var, ref.column)
        
        # Don't visit children to prevent duplicates
        return
    
    def visit_Attribute(self, node: ast.Attribute):
        """Handle df.column access (dot notation)."""
        ref = extract_dataframe_reference(node, self.df_tracker)
        if ref:
            # Ensure DataFrame is tracked
            self._ensure_dataframe_tracked(ref.df_var)
            
            # Check if column exists
            if self.check_column_exists(ref, node.lineno):
                # Mark as accessed
                self.schema.mark_accessed(ref.df_var, ref.column)
        
        # Don't visit children to prevent duplicates
        return
    
    # === RULE GROUP 2: Type Compatibility ===
    
    def infer_expression_type(self, node: ast.AST) -> Optional[DataType]:
        """
        Infer the data type of an expression.
        Supports DataFrame column references.
        """
        # DataFrame column access
        ref = extract_dataframe_reference(node, self.df_tracker)
        if ref:
            if self.schema.column_exists(ref.df_var, ref.column):
                symbol = self.schema.lookup_column(ref.df_var, ref.column)
                if symbol:
                    return symbol.data_type
        
        # Binary operation
        if isinstance(node, ast.BinOp):
            left_type = self.infer_expression_type(node.left)
            right_type = self.infer_expression_type(node.right)
            
            if left_type and right_type:
                if is_arithmetic_op(node.op):
                    if left_type.is_numeric() and right_type.is_numeric():
                        if left_type == DataType.INT and right_type == DataType.INT:
                            return DataType.INT
                        return DataType.FLOAT
        
        # Constants
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return DataType.INT
            elif isinstance(node.value, float):
                return DataType.FLOAT
            elif isinstance(node.value, str):
                return DataType.STRING
            elif isinstance(node.value, bool):
                return DataType.BOOL
        
        # Aggregations
        if isinstance(node, ast.Call):
            is_agg, _, _ = is_aggregation_call(node, self.df_tracker)
            if is_agg:
                return DataType.FLOAT
        
        return DataType.UNKNOWN
    
    def visit_BinOp(self, node: ast.BinOp):
        """Handle binary operations."""
        if not is_arithmetic_op(node.op):
            self.generic_visit(node)
            return
        
        left_type = self.infer_expression_type(node.left)
        right_type = self.infer_expression_type(node.right)
        
        op_str = get_binary_op_type(node.op) or "operation"
        
        # Check type compatibility
        if left_type and right_type:
            if not left_type.is_numeric():
                self.diagnostics.error(
                    f"Invalid arithmetic: cannot use '{op_str}' on type {left_type.value}",
                    node.lineno
                )
            elif not right_type.is_numeric():
                self.diagnostics.error(
                    f"Invalid arithmetic: cannot use '{op_str}' on type {right_type.value}",
                    node.lineno
                )
        
        # Check nullability
        self._check_nullable_in_expression(node.left, node.lineno)
        self._check_nullable_in_expression(node.right, node.lineno)
        
        self.generic_visit(node)
    
    # === RULE GROUP 3: Nullability ===
    
    def _check_nullable_in_expression(self, node: ast.AST, line: Optional[int] = None):
        """Check if nullable columns are used in risky operations."""
        ref = extract_dataframe_reference(node, self.df_tracker)
        if ref:
            if self.schema.column_exists(ref.df_var, ref.column):
                symbol = self.schema.lookup_column(ref.df_var, ref.column)
                if symbol and symbol.nullable:
                    self.diagnostics.warning(
                        f"Nullable column '{ref.column}' in DataFrame '{ref.df_var}' "
                        f"used in arithmetic operation",
                        line or self.current_line
                    )
    
    # === RULE GROUP 4: Aggregations ===
    
    def visit_Call(self, node: ast.Call):
        """Handle function calls, particularly aggregations."""
        is_agg, agg_func, ref = is_aggregation_call(node, self.df_tracker)
        
        if is_agg and ref:
            # Ensure DataFrame is tracked
            self._ensure_dataframe_tracked(ref.df_var)
            
            # Check column exists
            if self.check_column_exists(ref, node.lineno):
                # Mark as accessed
                self.schema.mark_accessed(ref.df_var, ref.column)
                
                symbol = self.schema.lookup_column(ref.df_var, ref.column)
                
                # Check type compatibility
                if symbol and not symbol.data_type.is_numeric():
                    self.diagnostics.error(
                        f"Cannot apply {agg_func}() to non-numeric column '{ref.column}' "
                        f"of type {symbol.data_type.value} in DataFrame '{ref.df_var}'",
                        node.lineno
                    )
                
                # Warn about nullability
                if symbol and symbol.nullable:
                    self.diagnostics.warning(
                        f"Aggregation {agg_func}() on nullable column '{ref.column}' "
                        f"in DataFrame '{ref.df_var}' may produce unexpected results",
                        node.lineno
                    )
            
            # Don't visit children
            return
        
        self.generic_visit(node)
    
    # === RULE GROUP 5: Derived Columns ===
    
    def visit_Assign(self, node: ast.Assign):
        """Handle assignments, particularly derived column creation."""
        is_col_assign, ref = is_assignment_to_column(node, self.df_tracker)
        
        if is_col_assign and ref:
            # Ensure DataFrame is tracked
            self._ensure_dataframe_tracked(ref.df_var)
            
            # Infer type from RHS
            derived_type = self.infer_expression_type(node.value)
            
            # Add to schema
            if not self.schema.column_exists(ref.df_var, ref.column):
                self.schema.add_derived_column(ref.df_var, ref.column, derived_type, node.lineno)
        
        # Visit RHS only
        self.visit(node.value)
        return
    
    # === Additional Handlers ===
    
    def visit_Compare(self, node: ast.Compare):
        """Handle comparison operations."""
        all_nodes = [node.left] + node.comparators
        
        for expr_node in all_nodes:
            refs = extract_all_column_references(expr_node, self.df_tracker)
            for ref in refs:
                self._ensure_dataframe_tracked(ref.df_var)
                if self.check_column_exists(ref, node.lineno):
                    self.schema.mark_accessed(ref.df_var, ref.column)
        
        self.generic_visit(node)
    
    # === Function Handling ===
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions."""
        self.function_depth += 1
        self.in_function = True
        self.generic_visit(node)
        self.function_depth -= 1
        if self.function_depth == 0:
            self.in_function = False
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        self.function_depth += 1
        self.in_function = True
        self.generic_visit(node)
        self.function_depth -= 1
        if self.function_depth == 0:
            self.in_function = False