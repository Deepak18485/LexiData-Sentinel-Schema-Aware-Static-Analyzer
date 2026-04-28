"""
LexiData-Sentinel Enhanced: Main Driver
Orchestrates analysis with support for multiple DataFrames and general code patterns.
"""

import ast
import sys
import argparse
from pathlib import Path

from diagnostics import DiagnosticCollector
from schema_loader import MultiDataFrameSchema, DataFrameSchema
from analyzer import EnhancedSemanticAnalyzer
from optimizer import EnhancedDeadColumnOptimizer
from ast_utils import detect_dataframes_in_code, DataFrameDetector


class LexiDataSentinelEnhanced:
    """
    Enhanced compiler driver for static analysis of DataFrame code.
    Supports multiple DataFrames, dot notation, and general code patterns.
    """
    
    def __init__(
        self,
        source_path: str,
        schema_path: str,
        verbose: bool = False,
        auto_detect: bool = True
    ):
        self.source_path = source_path
        self.schema_path = schema_path
        self.verbose = verbose
        self.auto_detect = auto_detect
        self.diagnostics = DiagnosticCollector()
    
    def run(self) -> bool:
        """Execute the complete analysis pipeline."""
        print("=" * 70)
        print("LexiData-Sentinel:Schema-Aware-Static-Analyzer")
        print("=" * 70)
        print()
        
        # Phase 1: Load source code
        print("[Phase 1] Loading source code...")
        source_code = self._load_source()
        if source_code is None:
            return False
        print(f"  ✓ Loaded {len(source_code)} characters from {self.source_path}")
        
        # Phase 2: Parse to AST
        print("[Phase 2] Parsing to Abstract Syntax Tree...")
        tree = self._parse_to_ast(source_code)
        if tree is None:
            return False
        print(f"  ✓ Successfully parsed AST")
        
        # Phase 3: Auto-detect DataFrames (if enabled)
        df_tracker = None
        if self.auto_detect:
            print("[Phase 3] Auto-detecting DataFrame variables...")
            detector = DataFrameDetector()
            detector.visit(tree)
            df_tracker = detector.tracker
            df_tracker._detector = detector  # attach so _load_schema can access inferred schemas

            detected_dfs = df_tracker.get_all_dataframes()
            if detected_dfs:
                print(f"  ✓ Detected {len(detected_dfs)} DataFrame variable(s): {', '.join(sorted(detected_dfs))}")
            else:
                print(f"  ⚠ No DataFrame variables auto-detected (will use schema defaults)")

            if self.verbose:
                for df_name in sorted(detected_dfs):
                    print(f"      - {df_name}")
        
        # Phase 4: Load schema
        print(f"[Phase {4 if self.auto_detect else 3}] Loading schema...")
        schema = self._load_schema(df_tracker)
        if schema is None:
            return False
        
        total_cols = sum(len(s.columns) for s in schema.schemas.values())
        print(f"  ✓ Loaded schema with {len(schema.schemas)} DataFrame(s), {total_cols} total column(s)")
        if self.verbose:
            for df_name, df_schema in schema.schemas.items():
                print(f"      - {df_name}: {len(df_schema.columns)} columns")
        
        # Phase 5: Semantic analysis
        print(f"[Phase {5 if self.auto_detect else 4}] Running semantic analysis...")
        self._run_semantic_analysis(tree, schema, df_tracker)
        print(f"  ✓ Semantic analysis complete")
        
        # Phase 6: Optimization passes
        print(f"[Phase {6 if self.auto_detect else 5}] Running optimization passes...")
        self._run_optimizations(schema)
        print(f"  ✓ Optimization complete")
        
        # Report diagnostics
        print()
        print("=" * 70)
        print("DIAGNOSTICS")
        print("=" * 70)
        print()
        
        if not self.diagnostics.diagnostics:
            print("✓ No issues found! Code looks good.")
        else:
            self.diagnostics.print_all()
        
        print()
        print("=" * 70)
        
        return not self.diagnostics.has_errors()
    
    def _load_source(self) -> str:
        """Load Python source code from file."""
        try:
            with open(self.source_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.diagnostics.error(f"Source file not found: {self.source_path}")
            return None
        except Exception as e:
            self.diagnostics.error(f"Error reading source file: {e}")
            return None
    
    def _parse_to_ast(self, source_code: str) -> ast.AST:
        """Parse source code into AST."""
        try:
            return ast.parse(source_code, filename=self.source_path)
        except SyntaxError as e:
            self.diagnostics.error(
                f"Syntax error in source code: {e.msg}",
                e.lineno
            )
            return None
        except Exception as e:
            self.diagnostics.error(f"Error parsing source code: {e}")
            return None
    
    def _load_schema(self, df_tracker) -> MultiDataFrameSchema:
        """Load schema from JSON file."""
        try:
            schema = MultiDataFrameSchema.from_multi_json(self.schema_path)

            print("  [DEBUG] Checking df_tracker...")
            if df_tracker and hasattr(df_tracker, '_detector'):
                MultiDataFrameSchema.register_inferred(
                    df_tracker._detector.inferred_schemas, schema
                )
                print("  [DEBUG] register_inferred done")
                if self.verbose:
                    for df_name in df_tracker._detector.inferred_schemas:
                        if schema.has_dataframe(df_name):
                            print(f"  ℹ Auto-registered '{df_name}' from source code")
            else:
                print("  [DEBUG] df_tracker has no _detector attribute")

            print("  [DEBUG] _load_schema complete")
            return schema

        except FileNotFoundError:
            self.diagnostics.error(f"Schema file not found: {self.schema_path}")
            return None
        except Exception as e:
            print(f"  [DEBUG] Exception caught: {type(e).__name__}: {e}")
            try:
                print("  [DEBUG] Trying from_json fallback...")
                return MultiDataFrameSchema.from_json(self.schema_path)
            except Exception as e2:
                print(f"  [DEBUG] Fallback also failed: {e2}")
                self.diagnostics.error(f"Error loading schema: {e}")
                return None
    
    def _run_semantic_analysis(self, tree: ast.AST, schema: MultiDataFrameSchema, df_tracker):
        """Execute semantic analysis pass."""
        analyzer = EnhancedSemanticAnalyzer(schema, self.diagnostics, df_tracker)
        analyzer.analyze(tree)
    
    def _run_optimizations(self, schema: MultiDataFrameSchema):
        """Execute optimization passes."""
        optimizer = EnhancedDeadColumnOptimizer(schema, self.diagnostics)
        optimizer.optimize()


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="LexiData-Sentinel Enhanced: Advanced DataFrame static analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Features:
  - Multiple DataFrame variables (df, data, customers, etc.)
  - Both subscript (df["col"]) and dot notation (df.col)
  - Auto-detection of DataFrame variables
  - Method chaining support
  - Function and control flow awareness

Example:
    python main_enhanced.py example.py schema.json
    python main_enhanced.py example.py schema.json --verbose
    python main_enhanced.py example.py schema.json --no-auto-detect
        """
    )
    
    parser.add_argument(
        "source",
        help="Path to Python source file to analyze"
    )
    
    parser.add_argument(
        "schema",
        help="Path to JSON schema file"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable automatic DataFrame variable detection"
    )
    
    args = parser.parse_args()
    
    sentinel = LexiDataSentinelEnhanced(
        args.source,
        args.schema,
        args.verbose,
        auto_detect=not args.no_auto_detect
    )
    success = sentinel.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()