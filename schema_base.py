# LexiData-Sentinel: Base Schema Classes
# DataType enum and ColumnSymbol class - imported by all modules

from enum import Enum
from typing import Optional


class DataType(Enum):
    """DataFrame column data types."""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "bool" 
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, type_str: str) -> 'DataType':
        """Convert string to DataType."""
        type_str = type_str.lower()
        if type_str in ["int", "integer"]:
            return cls.INT
        elif type_str in ["float", "double"]:
            return cls.FLOAT
        elif type_str in ["string", "str"]:
            return cls.STRING
        elif type_str in ["bool", "boolean"]:
            return cls.BOOL
        return cls.UNKNOWN

    def is_numeric(self) -> bool:
        """Check if type supports arithmetic."""
        return self in [self.INT, self.FLOAT]

    def is_int(self) -> bool:
        """Check if integer type."""
        return self == self.INT


class ColumnSymbol:
    """Represents a DataFrame column in the symbol table."""
    
    def __init__(
        self, 
        name: str, 
        data_type: DataType, 
        nullable: bool = False, 
        is_derived: bool = False
    ):
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.is_derived = is_derived
        self.access_count = 0
        self.defined_at_line: Optional[int] = None

    def mark_accessed(self):
        """Mark column as read."""
        self.access_count += 1

    def is_dead(self) -> bool:
        """Check if derived column was never used."""
        return self.is_derived and self.access_count == 0

    def __repr__(self) -> str:
        status = "derived" if self.is_derived else "schema"
        null_str = "nullable" if self.nullable else "non-null"
        return f"Column({self.name}:{self.data_type.value} {status} {null_str})"
