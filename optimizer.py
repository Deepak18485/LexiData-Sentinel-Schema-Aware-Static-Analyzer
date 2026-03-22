"""
LexiData-Sentinel Enhanced: Multi-DataFrame Optimizer
Performs optimization passes on multiple DataFrames.
"""

from diagnostics import DiagnosticCollector
from schema_loader import MultiDataFrameSchema


class EnhancedDeadColumnOptimizer:
    """
    Performs dead code elimination analysis on multiple DataFrames.
    """
    
    def __init__(self, schema: MultiDataFrameSchema, diagnostics: DiagnosticCollector):
        self.schema = schema
        self.diagnostics = diagnostics
    
    def optimize(self):
        """Run all optimization passes."""
        self._detect_dead_derived_columns()
        self._detect_unused_schema_columns()
    
    def _detect_dead_derived_columns(self):
        """Detect derived columns that are defined but never used."""
        for df_name in self.schema.get_all_dataframes():
            df_schema = self.schema.get_schema(df_name)
            if df_schema:
                dead_columns = df_schema.get_dead_columns()
                
                for col in dead_columns:
                    line_info = f" (defined at line {col.defined_at_line})" if col.defined_at_line else ""
                    self.diagnostics.info(
                        f"Derived column '{col.name}' in DataFrame '{df_name}' "
                        f"is defined but never used{line_info}"
                    )
    
    def _detect_unused_schema_columns(self):
        """Detect schema columns that are never accessed."""
        for df_name in self.schema.get_all_dataframes():
            df_schema = self.schema.get_schema(df_name)
            if df_schema:
                unused_columns = df_schema.get_unused_schema_columns()
                
                for col in unused_columns:
                    self.diagnostics.info(
                        f"Schema column '{col.name}' in DataFrame '{df_name}' "
                        f"is never accessed in code"
                    )