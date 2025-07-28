from fastapi import APIRouter, Depends, HTTPException, Request
from src.presentation.api.schemas.price_schemas import PriceResponse, ErrorResponse
from src.presentation.api.dependencies import get_price_use_case
from src.application.use_cases.get_price import GetPriceUseCase
from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"model": ErrorResponse}}
)


@router.get(
    "/{symbol}-{vs_currency}",
    response_model=PriceResponse,
    summary="Get current cryptocurrency price",
    description="Get the current price for a cryptocurrency pair (e.g., eth-usdt)"
)
async def get_crypto_price(
    symbol: str,
    vs_currency: str,
    request: Request,
    use_case: GetPriceUseCase = Depends(get_price_use_case)
):
    """Get current price for a cryptocurrency pair"""
    try:
        price = await use_case.execute(symbol, vs_currency)
        
        if not price:
            raise HTTPException(
                status_code=404,
                detail=f"Price not found for pair {symbol}/{vs_currency}"
            )
        
        return PriceResponse(**price.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching price"
        )


@router.get(
    "/eth-usdt",
    response_model=PriceResponse,
    summary="Get ETH/USDT price",
    description="Shortcut endpoint for ETH/USDT pair"
)
async def get_eth_usdt_price(
    request: Request,
    use_case: GetPriceUseCase = Depends(get_price_use_case)
):
    """Get current ETH/USDT price"""
    return await get_crypto_price("eth", "usdt", request, use_case)