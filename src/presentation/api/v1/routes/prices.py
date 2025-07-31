from fastapi import APIRouter, Depends, HTTPException, Path
from src.presentation.api.v1.schemas.response import PriceResponse
from src.presentation.api.dependencies import get_price_service
from src.services.price_service import PriceService
from src.shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/{pair}", response_model=PriceResponse)
async def get_crypto_price(
    pair: str = Path(..., description="Cryptocurrency pair (e.g., eth-usdt, btc-usd)"),
    price_service: PriceService = Depends(get_price_service)
) -> PriceResponse:
    """Get current price for a cryptocurrency pair"""
    try:
        # Parse the pair format: symbol-vs_currency
        parts = pair.lower().split('-')
        if len(parts) != 2:
            raise HTTPException(
                status_code=400,
                detail="Invalid pair format. Use format: symbol-currency (e.g., eth-usdt)"
            )
        
        symbol, vs_currency = parts
        
        # Get price from service
        price_model = await price_service.get_current_price(symbol, vs_currency)
        
        if not price_model:
            raise HTTPException(
                status_code=404,
                detail=f"Price not found for {symbol}/{vs_currency}"
            )
        
        return PriceResponse(
            symbol=price_model.symbol,
            vs_currency=price_model.vs_currency,
            price=price_model.price,
            volume_24h=price_model.volume_24h,
            price_change_24h=price_model.price_change_24h,
            last_updated=price_model.last_updated,
            fetched_at=price_model.fetched_at,
            pair=f"{price_model.symbol.upper()}/{price_model.vs_currency.upper()}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price for {pair}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching price"
        )