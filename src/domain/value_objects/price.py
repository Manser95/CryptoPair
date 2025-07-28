from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass(frozen=True)
class Price:
    value: Decimal
    
    def __init__(self, value: Union[float, str, Decimal]):
        if isinstance(value, (float, int)):
            object.__setattr__(self, 'value', Decimal(str(value)))
        elif isinstance(value, str):
            object.__setattr__(self, 'value', Decimal(value))
        elif isinstance(value, Decimal):
            object.__setattr__(self, 'value', value)
        else:
            raise ValueError(f"Invalid price value type: {type(value)}")
            
        if self.value < 0:
            raise ValueError("Price cannot be negative")
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __float__(self) -> float:
        return float(self.value)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Price):
            return self.value == other.value
        return False
    
    def __lt__(self, other) -> bool:
        if isinstance(other, Price):
            return self.value < other.value
        return NotImplemented