import pytest
from datetime import datetime
from src.domain.entities.crypto_price import CryptoPrice


class TestCryptoPrice:
    """Test cases for CryptoPrice entity"""
    
    def test_crypto_price_creation(self):
        """Test creating a CryptoPrice instance"""
        price = CryptoPrice(
            symbol="btc",
            vs_currency="usd",
            price=45000.50,
            volume_24h=50000000.0,
            price_change_24h=2.5,
            last_updated=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        assert price.symbol == "btc"
        assert price.vs_currency == "usd"
        assert price.price == 45000.50
        assert price.volume_24h == 50000000.0
        assert price.price_change_24h == 2.5
        assert price.last_updated == datetime(2024, 1, 1, 12, 0, 0)
    
    def test_crypto_price_minimal(self):
        """Test creating CryptoPrice with minimal required fields"""
        price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=2500.0
        )
        
        assert price.symbol == "eth"
        assert price.vs_currency == "usdt"
        assert price.price == 2500.0
        assert price.volume_24h is None
        assert price.price_change_24h is None
        assert price.last_updated is None
    
    def test_pair_name_property(self):
        """Test pair_name property returns correct format"""
        price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=2500.0
        )
        
        assert price.pair_name == "ETH/USDT"
    
    def test_pair_name_uppercase(self):
        """Test pair_name handles uppercase symbols"""
        price = CryptoPrice(
            symbol="BTC",
            vs_currency="USD",
            price=45000.0
        )
        
        assert price.pair_name == "BTC/USD"
    
    def test_to_dict_full(self):
        """Test to_dict method with all fields"""
        last_updated = datetime(2024, 1, 1, 12, 0, 0)
        price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=2500.50,
            volume_24h=1000000.0,
            price_change_24h=5.25,
            last_updated=last_updated
        )
        
        result = price.to_dict()
        
        assert result == {
            "symbol": "eth",
            "vs_currency": "usdt",
            "price": 2500.50,
            "volume_24h": 1000000.0,
            "price_change_24h": 5.25,
            "last_updated": last_updated.isoformat(),
            "pair": "ETH/USDT"
        }
    
    def test_to_dict_minimal(self):
        """Test to_dict method with minimal fields"""
        price = CryptoPrice(
            symbol="btc",
            vs_currency="usd",
            price=45000.0
        )
        
        result = price.to_dict()
        
        assert result == {
            "symbol": "btc",
            "vs_currency": "usd",
            "price": 45000.0,
            "volume_24h": None,
            "price_change_24h": None,
            "last_updated": None,
            "pair": "BTC/USD"
        }
    
    def test_to_dict_preserves_types(self):
        """Test that to_dict preserves data types correctly"""
        price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=2500.123456,
            volume_24h=1000000.789,
            price_change_24h=-5.25
        )
        
        result = price.to_dict()
        
        assert isinstance(result["price"], float)
        assert isinstance(result["volume_24h"], float)
        assert isinstance(result["price_change_24h"], float)
        assert result["price_change_24h"] == -5.25