import requests
import logging
from pybit.unified_trading import HTTP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

api_key = 'ULI4j96SQhGePVhxCu'
api_secret = 'XnBhumm73kDKJSFDFLKEZSLkkX2KwMvAj4qC'
session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)

def check_positions():
    symbols = ['1000IQ50USDT']  # Add the symbols you want to check positions for
    processed_positions = {}  # Keep track of processed positions
    while True:
        try:
            for symbol in symbols:
                positions = session.get_positions(category="linear", symbol=symbol)['result']['list']

                if positions:
                    position = positions[0]  # Get the first position for the symbol
                    symbol = position['symbol']

                    if 'unrealisedPnl' not in position or position['unrealisedPnl'] == '':
                        continue

                    unrealised_pnl = float(position['unrealisedPnl'])

                    if 'size' in position and position['size'] != '':
                        size = float(position['size'])
                    else:
                        continue
                    print(unrealised_pnl)
                    if unrealised_pnl >= 0.2:
                        logger.info(f"Win")
                        close_position(symbol, size)
                else:
                    logger.info(f"No positions found for {symbol}")

        except Exception as e:
            logger.error(f"Error in check_positions: {str(e)}")

def take_partial_profit(symbol, qty, profit_percent):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        if position_info['result']['list']:
            side = "Buy" if position_info['result']['list'][0]['side'] == "Sell" else "Sell"
            qty_to_close = qty * profit_percent
            session.place_order(
                category="linear", symbol=symbol, side=side, orderType="Market", qty=qty_to_close)
    except Exception as e:
        logger.error(f"Error in take_partial_profit: {str(e)}")

def set_stop_loss(symbol):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        if position_info['result']['list']:
            position = position_info['result']['list'][0]
            if 'avgPrice' in position and position['avgPrice'] != '':
                avg_price = float(position['avgPrice'])

                session.set_trading_stop(
                    category="linear",
                    symbol=symbol,
                    stop_loss=str(avg_price)
                )
            else:
                logger.warning(f"Average price not found for {symbol}")
    except Exception as e:
        logger.error(f"Error in set_stop_loss: {str(e)}")

def close_position(symbol, qty):
    try:
        position_info = session.get_positions(category="linear", symbol=symbol)
        if position_info['result']['list']:
            side = "Buy" if position_info['result']['list'][0]['side'] == "Sell" else "Sell"
            session.place_order(
                category="linear", symbol=symbol, side=side, orderType="Market", qty=qty)
    except Exception as e:
        logger.error(f"Error in close_position: {str(e)}")


url = "http://127.0.0.1:8000/webhook"
payload = {
  "action": "sell",
  "symbol": "DOGEUSDT"
}
params = {
    "passphrase": "Armjansk12!!"
}

response = requests.post(url, json=payload, params=params)
print(response.text)

if __name__ == "__main__":
    check_positions()