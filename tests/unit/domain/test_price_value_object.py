import pytest
from decimal import Decimal
from src.domain.value_objects.price import Price


class TestPriceValueObject:
    """Test cases for Price value object"""
    
    def test_price_from_float(self):
        """Test creating Price from float"""
        price = Price(100.50)
        assert price.value == Decimal("100.50")
    
    def test_price_from_int(self):
        """Test creating Price from integer"""
        price = Price(100)
        assert price.value == Decimal("100")
    
    def test_price_from_string(self):
        """Test creating Price from string"""
        price = Price("100.50")
        assert price.value == Decimal("100.50")
    
    def test_price_from_decimal(self):
        """Test creating Price from Decimal"""
        decimal_value = Decimal("100.50")
        price = Price(decimal_value)
        assert price.value == decimal_value
    
    def test_price_negative_value_raises_error(self):
        """Test that negative price raises ValueError"""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Price(-10.0)
    
    def test_price_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError"""
        with pytest.raises(ValueError, match="Invalid price value type"):
            Price([100])
    
    def test_price_is_immutable(self):
        """Test that Price is immutable (frozen dataclass)"""
        price = Price(100.0)
        with pytest.raises(AttributeError):
            price.value = Decimal("200")
    
    def test_price_str_representation(self):
        """Test string representation of Price"""
        price = Price(100.50)
        assert str(price) == "100.50"
    
    def test_price_float_conversion(self):
        """Test converting Price to float"""
        price = Price(100.50)
        assert float(price) == 100.50
        assert isinstance(float(price), float)
    
    def test_price_equality(self):
        """Test Price equality comparison"""
        price1 = Price(100.50)
        price2 = Price("100.50")
        price3 = Price(200.0)
        
        assert price1 == price2
        assert price1 != price3
        assert price1 != 100.50  # Not equal to non-Price objects
    
    def test_price_less_than_comparison(self):
        """Test Price less than comparison"""
        price1 = Price(100.0)
        price2 = Price(200.0)
        
        assert price1 < price2
        assert not price2 < price1
        assert not price1 < price1
    
    def test_price_comparison_with_non_price_returns_not_implemented(self):
        """Test that comparing with non-Price returns NotImplemented"""
        price = Price(100.0)
        result = price.__lt__(100.0)
        assert result == NotImplemented
    
    def test_price_precision_handling(self):
        """Test that Price handles decimal precision correctly"""
        price = Price(0.1 + 0.2)  # Known float precision issue
        # Should be handled correctly through string conversion
        assert price.value == Decimal("0.30000000000000004") or price.value == Decimal("0.3")
        
        # Better to use string for precise values
        price_precise = Price("0.3")
        assert price_precise.value == Decimal("0.3")