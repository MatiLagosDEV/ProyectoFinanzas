from fastapi import APIRouter
import yfinance as yf

router = APIRouter(prefix="/dividendos", tags=["Dividendos"])

@router.get("/{ticker}")
def obtener_dividendos(ticker: str):
    try:
        data = yf.Ticker(ticker)
        dividendos = data.dividends.to_dict()
        return {"ticker": ticker, "dividendos": dividendos}
    except Exception:
        return {"error": "No se pudo obtener dividendos"}
