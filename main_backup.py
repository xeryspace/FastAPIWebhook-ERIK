import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from pybit.unified_trading import HTTP
from threading import Lock

position_lock = Lock()
position_processing = {}

app = FastAPI()

api_key = 'ULI4j96SQhGePVhxCu'
api_secret = 'XnBhumm73kDKJSFDFLKEZSLkkX2KwMvAj4qC'
session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.get("/")
async def read_root():
    return {"name": "my-app", "version": "Hello world! From FastAPI running on Uvicorn."}

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        query_params = dict(request.query_params)
        passphrase = query_params.get("passphrase", "")
        if passphrase != "Armjansk12!!":
            raise HTTPException(status_code=403, detail="Invalid passphrase")

        body = await request.json()
        symbol = body.get("symbol")  # Get the symbol like 'DEGENUSDT' or 'WIFUSDT'
        qty = body.get("qty")
        action = body.get("action")

        if action not in ['buy', 'sell']:
            return {"status": "ignored", "reason": f"Invalid action: {action}"}

        logger.info(f"Received {action} action for {symbol}")

        # Get the entry price from the Bybit API
        entry_price = get_current_price(symbol)

        await process_signal(symbol, qty, action, entry_price)
        return {"status": "success", "data": "Position updated"}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in the alert message: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON format in the alert message")
    except Exception as e:
        logger.error(f"Error in handle_webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def check_position_exists(symbol):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        if position_info['result']['list']:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error in check_position_exists: {str(e)}")
        raise

def get_current_price(symbol):
    try:
        ticker = session.get_tickers(category="linear", symbol=symbol)
        if ticker['result']:
            last_price = float(ticker['result']['list'][0]['lastPrice'])
            return last_price
        else:
            raise Exception(f"Failed to retrieve current price for {symbol}")
    except Exception as e:
        logger.error(f"Error in get_current_price: {str(e)}")
        raise

def open_position(side, symbol, qty):
    try:
        session.place_order(
            category="linear", symbol=symbol, side=side, orderType="Market", qty=qty)
    except Exception as e:
        logger.error(f"Error in open_position: {str(e)}")
        raise

def close_position(symbol, qty):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        if position_info['result']['list']:
            side = "Buy" if position_info['result']['list'][0]['side'] == "Sell" else "Sell"
            session.place_order(
                category="linear", symbol=symbol, side=side, orderType="Market", qty=qty)
    except Exception as e:
        logger.error(f"Error in close_position: {str(e)}")
        raise

async def process_signal(symbol, qty, action, entry_price):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        current_position = None
        current_qty = 0
        if position_info['result']['list']:
            current_position = position_info['result']['list'][0]['side']
            current_qty = float(position_info['result']['list'][0]['size'])
        logger.info(f"Current position for {symbol}: {current_position}, Quantity: {current_qty}")

        if current_position is None or current_position == "":
            if action == "buy":
                logger.info(f"Opening new Buy position for {symbol}")
                open_position('Buy', symbol, qty)
            elif action == "sell":
                logger.info(f"Ignoring Sell signal as there is no open position for {symbol}")
        elif current_position == "Buy":
            if action == "sell":
                logger.info(f"Closing Buy position for {symbol}")
                close_position(symbol, current_qty)
        elif current_position == "Sell":
            if action == "buy":
                logger.info(f"Closing Sell position and opening Buy position for {symbol}")
                close_position(symbol, current_qty)
                open_position('Buy', symbol, qty)
    except Exception as e:
        logger.error(f"Error in process_signal: {str(e)}")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)