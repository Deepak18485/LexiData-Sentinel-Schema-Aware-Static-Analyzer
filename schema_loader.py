"""
LexiData-Sentinel Enhanced: Multi-DataFrame Schema Loader
Supports multiple DataFrames with separate schemas for each.
"""

import json
from typing import Dict, Optional, Set
from schema_base import DataType, ColumnSymbol


class MultiDataFrameSchema:
    """
    Manages schemas for multiple DataFrames.
    Each DataFrame variable has its own schema/symbol table.
    """
    
    def __init__(self):
        self.schemas: Dict[str, 'DataFrameSchema'] = {}
        self.default_df_name = "df"
    
    def add_dataframe(self, df_name: str, schema: 'DataFrameSchema'):
        """Add a schema for a specific DataFrame variable."""
        self.schemas[df_name] = schema
    
    def get_schema(self, df_name: str) -> Optional['DataFrameSchema']:
        """Get schema for a specific DataFrame."""
        return self.schemas.get(df_name)
    
    def has_dataframe(self, df_name: str) -> bool:
        """Check if a DataFrame schema exists."""
        return df_name in self.schemas
    
    def lookup_column(self, df_name: str, column_name: str) -> Optional[ColumnSymbol]:
        """Look up a column in a specific DataFrame."""
        schema = self.get_schema(df_name)
        if schema:
            return schema.lookup(column_name)
        return None
    
    def column_exists(self, df_name: str, column_name: str) -> bool:
        """Check if a column exists in a DataFrame."""
        schema = self.get_schema(df_name)
        if schema:
            return schema.exists(column_name)
        return False
    
    def add_derived_column(self, df_name: str, column_name: str, data_type: DataType, line: Optional[int] = None):
        """Add a derived column to a DataFrame."""
        schema = self.get_schema(df_name)
        if schema:
            schema.add_derived_column(column_name, data_type, line)
        else:
            # Auto-create schema if it doesn't exist
            schema = DataFrameSchema(df_name)
            schema.add_derived_column(column_name, data_type, line)
            self.add_dataframe(df_name, schema)
    
    def mark_accessed(self, df_name: str, column_name: str):
        """Mark a column as accessed."""
        schema = self.get_schema(df_name)
        if schema:
            symbol = schema.lookup(column_name)
            if symbol:
                symbol.mark_accessed()
    
    def get_all_dataframes(self) -> Set[str]:
        """Get all DataFrame variable names."""
        return set(self.schemas.keys())
    
    @classmethod
    def from_json(cls, schema_path: str, df_name: str = "df") -> 'MultiDataFrameSchema':
        """
        Load schema from JSON for a single DataFrame.
        
        Args:
            schema_path: Path to JSON schema file
            df_name: DataFrame variable name (default: "df")
        """
        multi_schema = cls()
        df_schema = DataFrameSchema.from_json(schema_path, df_name)
        multi_schema.add_dataframe(df_name, df_schema)
        return multi_schema
    
    @classmethod
    def from_multi_json(cls, schema_path: str) -> 'MultiDataFrameSchema':
        """
        Load schemas for multiple DataFrames from a JSON file.
        
        JSON format:
        {
          "dataframes": {
            "df": {
              "columns": [...]
            },
            "customers": {
              "columns": [...]
            }
          }
        }
        """
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        multi_schema = cls()
        
        # Check if it's multi-DataFrame format
        if "dataframes" in data:
            for df_name, df_data in data["dataframes"].items():
                schema = DataFrameSchema(df_name)
                for col_def in df_data.get("columns", []):
                    name = col_def["name"]
                    data_type = DataType.from_string(col_def["type"])
                    nullable = col_def.get("nullable", False)
                    symbol = ColumnSymbol(name, data_type, nullable, is_derived=False)
                    schema.columns[name] = symbol
                    schema._original_columns.add(name)
                multi_schema.add_dataframe(df_name, schema)
        else:
            # Single DataFrame format (backward compatible)
            df_schema = DataFrameSchema.from_dict(data, "df")
            multi_schema.add_dataframe("df", df_schema)
        
        return multi_schema


class DataFrameSchema:
    """
    Schema for a single DataFrame.
    Similar to SchemaTable but with DataFrame name.
    """
    
    def __init__(self, df_name: str = "df"):
        self.df_name = df_name
        self.columns: Dict[str, ColumnSymbol] = {}
        self._original_columns: Set[str] = set()
    
    @classmethod
    def from_json(cls, schema_path: str, df_name: str = "df") -> 'DataFrameSchema':
        """Load schema from JSON file."""
        with open(schema_path, 'r') as f:
            schema_data = json.load(f)
        return cls.from_dict(schema_data, df_name)
    
    @classmethod
    def from_dict(cls, schema_dict: dict, df_name: str = "df") -> 'DataFrameSchema':
        """Load schema from dictionary."""
        schema = cls(df_name)
        
        for col_def in schema_dict.get("columns", []):
            name = col_def["name"]
            data_type = DataType.from_string(col_def["type"])
            nullable = col_def.get("nullable", False)
            
            symbol = ColumnSymbol(name, data_type, nullable, is_derived=False)
            schema.columns[name] = symbol
            schema._original_columns.add(name)
        
        return schema
    
    def lookup(self, column_name: str) -> Optional[ColumnSymbol]:
        """Look up a column."""
        return self.columns.get(column_name)
    
    def exists(self, column_name: str) -> bool:
        """Check if a column exists."""
        return column_name in self.columns
    
    def add_derived_column(self, name: str, data_type: DataType, line: Optional[int] = None):
        """Add a derived column."""
        symbol = ColumnSymbol(name, data_type, nullable=False, is_derived=True)
        symbol.defined_at_line = line
        self.columns[name] = symbol
    
    def get_dead_columns(self) -> list[ColumnSymbol]:
        """Get derived columns that were never used."""
        return [col for col in self.columns.values() if col.is_dead()]
    
    def get_unused_schema_columns(self) -> list[ColumnSymbol]:
        """Get schema columns that were never accessed."""
        return [
            self.columns[name] for name in self._original_columns
            if self.columns[name].access_count == 0
        ]
    
    def __repr__(self):
        return f"DataFrameSchema({self.df_name}, {len(self.columns)} columns)"