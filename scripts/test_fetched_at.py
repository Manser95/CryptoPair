#!/usr/bin/env python
"""Test script to verify fetched_at field works correctly"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_access.models.price_model import PriceModel


async def test_price_model():
    """Test that PriceModel works with new fetched_at field"""
    
    print("🧪 Testing PriceModel with fetched_at field")
    print("=" * 50)
    
    # Test 1: Create model with fetched_at
    now = datetime.utcnow()
    coingecko_time = datetime(2025, 7, 31, 10, 37, 46)
    
    price = PriceModel(
        symbol="eth",
        vs_currency="usdt", 
        price=3859.33,
        volume_24h=32895700837.0,
        price_change_24h=1.58,
        last_updated=coingecko_time,
        fetched_at=now
    )
    
    print("✅ Created PriceModel with fetched_at field")
    print(f"   Symbol: {price.symbol}")
    print(f"   Price: ${price.price:,.2f}")
    print(f"   CoinGecko last updated: {price.last_updated}")
    print(f"   Fetched by us at: {price.fetched_at}")
    
    # Test 2: Convert to dict
    data_dict = price.to_dict()
    print(f"\n✅ Converted to dict:")
    print(f"   last_updated: {data_dict['last_updated']}")
    print(f"   fetched_at: {data_dict['fetched_at']}")
    
    # Test 3: Convert back from dict
    price_from_dict = PriceModel.from_dict(data_dict)
    print(f"\n✅ Converted back from dict:")
    print(f"   Original fetched_at: {price.fetched_at}")
    print(f"   Restored fetched_at: {price_from_dict.fetched_at}")
    print(f"   Match: {price.fetched_at == price_from_dict.fetched_at}")
    
    print(f"\n🎉 All tests passed! New fetched_at field works correctly.")


if __name__ == "__main__":
    asyncio.run(test_price_model())