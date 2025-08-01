import aiohttp
from typing import Optional, Dict, Any
from src.shared.config import settings
from src.shared.logging import get_logger
from src.shared.exceptions import RateLimitExceeded

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
                enable_cleanup_closed=True,
                force_close=False,  # Переиспользуем соединения
                keepalive_timeout=30,  # Keep-alive для соединений
                ssl=False  # Отключаем SSL проверку для скорости (только для тестирования!)
            )
            
            timeout = aiohttp.ClientTimeout(
                total=settings.coingecko_timeout,
                connect=settings.coingecko_connect_timeout,
                sock_read=settings.coingecko_read_timeout
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
        
        
        # Only log errors and rate limits, not every request
        
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
                
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit exceeded (429): url={url}, retry_after={retry_after}")
                raise RateLimitExceeded(retry_after)
            else:
                logger.error(f"HTTP response error: status={e.status}, message={e.message}, url={url}")
            raise
        except aiohttp.ClientTimeout as e:
            logger.error(f"HTTP request timeout: url={url}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}, url={url}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during HTTP request: {e}, url={url}")
            raise