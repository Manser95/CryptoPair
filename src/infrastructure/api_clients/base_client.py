import aiohttp
from typing import Optional, Dict, Any
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class BaseHttpClient:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=settings.aiohttp_total_connections,
                limit_per_host=settings.aiohttp_connections_per_host,
                ttl_dns_cache=settings.aiohttp_dns_ttl,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=settings.coingecko_timeout,
                connect=5,
                sock_read=25
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        session = await self._get_session()
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during HTTP request: {e}")
            raise