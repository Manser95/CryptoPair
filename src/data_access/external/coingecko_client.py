from typing import Dict, Any, Optional
from src.data_access.external.base_client import BaseHttpClient
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CoinGeckoClient(BaseHttpClient):
    def __init__(self):
        super().__init__()
        self.base_url = settings.coingecko_base_url
        self.api_key = settings.coingecko_api_key
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "CryptoPairsAPI/1.0"
        }
        
        # For Demo API, the key should be passed as query parameter
        # Headers are only for Pro API
        return headers
    
    async def get_simple_price(
        self, 
        ids: str, 
        vs_currencies: str,
        include_24hr_vol: bool = False,
        include_24hr_change: bool = False,
        include_last_updated_at: bool = True
    ) -> Dict[str, Any]:
        """
        Get current price of cryptocurrencies
        
        Args:
            ids: Comma-separated cryptocurrency ids (e.g., "ethereum")
            vs_currencies: Comma-separated vs currencies (e.g., "usd")
            include_24hr_vol: Include 24hr volume
            include_24hr_change: Include 24hr change
            include_last_updated_at: Include last updated timestamp
            
        Returns:
            Price data dictionary
        """
        endpoint = f"{self.base_url}/simple/price"
        
        params = {
            "ids": ids,
            "vs_currencies": vs_currencies
        }
        
        # Add Demo API key to params if available
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
        
        if include_24hr_vol:
            params["include_24hr_vol"] = "true"
        if include_24hr_change:
            params["include_24hr_change"] = "true"
        if include_last_updated_at:
            params["include_last_updated_at"] = "true"
        
        
        try:
            data = await self.request(
                method="GET",
                url=endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch price data: {e}")
            raise
    
    async def get_coin_market_chart(
        self,
        coin_id: str,
        vs_currency: str,
        days: int = 1,
        interval: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical market data
        
        Args:
            coin_id: Cryptocurrency id (e.g., "ethereum")
            vs_currency: Target currency (e.g., "usd")
            days: Data up to number of days ago
            interval: Data interval (daily/hourly)
            
        Returns:
            Historical market data
        """
        endpoint = f"{self.base_url}/coins/{coin_id}/market_chart"
        
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        # Add Demo API key to params if available
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
        
        if interval:
            params["interval"] = interval
            
        
        try:
            data = await self.request(
                method="GET",
                url=endpoint,
                headers=self._get_headers(),
                params=params
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch market chart data: {e}")
            raise