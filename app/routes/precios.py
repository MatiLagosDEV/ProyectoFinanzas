
from fastapi import APIRouter
import yfinance as yf
import requests

router = APIRouter(prefix="/precios", tags=["Precios"])


@router.get("/{ticker}/dividendos")
def obtener_dividendos_historicos(ticker: str):
    """
    Devuelve el histórico de dividendos pagados para el ticker dado usando yfinance.
    """
    try:
        data = yf.Ticker(ticker)
        dividendos = data.dividends
        lista = [
            {"fecha": str(idx.date()), "dividendo": float(valor)}
            for idx, valor in dividendos.items()
        ]
        return {"ticker": ticker, "dividendos": lista, "fuente": "yfinance"}
    except Exception as e:
        return {"error": f"No se pudo obtener el histórico de dividendos con yfinance: {str(e)}"}


@router.get("/{ticker}")
def obtener_precios_historicos(ticker: str):
    """
    Devuelve el histórico de precios de cierre de los últimos 5 días para el ticker dado usando yfinance.
    """
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="5d")
        def format_num(n):
            return f"{n:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        precios = [
            {"fecha": str(idx.date()), "close": format_num(round(float(row["Close"]), 2))}
            for idx, row in hist.iterrows()
        ]
        return {"ticker": ticker, "precios": precios, "fuente": "yfinance", "moneda": "CLP"}
    except Exception as e:
        return {"error": f"No se pudo obtener el histórico de precios con yfinance: {str(e)}"}
