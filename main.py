# Updated main.py for WebSocket chat integration
import aiohttp
import asyncio
import json
import names
import websockets
from aiofile import AIOFile
from datetime import datetime, timedelta
from abc import ABC, abstractclassmethod

FILENAME = 'exchange_logs.txt'

class FetchLogger():
    @staticmethod
    async def log_fetch(fname=FILENAME):
        async with AIOFile(fname, 'a') as afp:
            await afp.write(f"Exchange command executed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")




class AbstractFetcher(ABC):
    @abstractclassmethod
    def fetch_exchange_rates_archive(self, days_back, currencies):
        pass

    @abstractclassmethod
    def fetch_exchange_rates_current(self):
        pass

    @abstractclassmethod
    def extract_rates(self, *args):
        pass

class ExchangeRateFetcher(AbstractFetcher):
    async def fetch_exchange_rates_archive(self, days_back, currencies):
        async with aiohttp.ClientSession() as session:
            dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y') for i in range(days_back)]
            results = []

            for date in dates:
                url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = self.extract_rates(data, currencies)
                        results.append({date: rates})
                    else:
                        # Possible network errors handling
                        results.append({date: "Error fetching data"})

            return results
        
    async def fetch_exchange_rates_current(self):
        async with aiohttp.ClientSession() as session:                       
            result= ""
            url = 'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5'
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                else:
                    # Possible network errors handling
                    result = "Error fetching data"

            return result

    def extract_rates(self, data, currencies):
        rates = {}
        for currency in currencies:
            for item in data['exchangeRate']:
                if item['currency'] == currency:
                    rates[currency] = {
                        'sale': item.get('saleRate', item['saleRateNB']),
                        'purchase': item.get('purchaseRate', item['purchaseRateNB'])
                    }
                    break
        return rates

class Server:
    clients = set()

    async def register(self, ws: websockets.WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)

    async def unregister(self, ws: websockets.WebSocketServerProtocol):
        self.clients.remove(ws)

    async def send_to_clients(self, message):
        if self.clients:
            tasks = [client.send(message) for client in self.clients]
            await asyncio.gather(*tasks)
            # for client in self.clients:
            #     await client.send(json.dumps(message))

    async def ws_handler(self, ws, path):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws):        
        cur_list = ['CHF', 'EUR', 'GBP', 'PLZ', 'SEK', 'UAH', 'USD', 'XAU', 'CAD']
        async for message in ws:
             
            if message.startswith('exchange'):
                await self.send_to_clients(f"{ws.name}: {message}")  
                params = message.split()
                
                if len(params)>=2: #Check if there are enough parts in message
                    if params[1].isdigit():
                        unique_cur = set()
                        valid_cur_params = []
                        for index, item in enumerate(params[2:], start = 2):
                            if item in cur_list and item not in unique_cur:
                                valid_cur_params.append(item)
                                unique_cur.add(item)
                            elif item not in cur_list: 
                                await self.send_to_clients(f"Lst of currencies contains not available currency {item}. It was eliminated")
                                await self.send_to_clients(f"Should be in the following list: ['CHF', 'EUR', 'GBP', 'PLZ', 'SEK', 'UAH', 'USD', 'XAU', 'CAD']")
                        parts = params[:2] + valid_cur_params
                        days_back = int(parts[1])
                        currencies = parts[2:] if len(parts) > 2 else ['EUR', 'USD']
                        fetcher = ExchangeRateFetcher()
                        rates = await fetcher.fetch_exchange_rates_archive(days_back, currencies)
                        await FetchLogger.log_fetch(FILENAME)
                        response = json.dumps(rates, indent=2, ensure_ascii=False)
                        await self.send_to_clients(f"Reply from PrivatBank to {ws.name}:")
                        await self.send_to_clients(response)
                    else: 
                        await self.send_to_clients("Second parameter should be digit or no parameters should be provided after 'exchange' command")
                else:
                    fetcher = ExchangeRateFetcher()
                    rates = await fetcher.fetch_exchange_rates_current()
                    await FetchLogger.log_fetch(FILENAME)
                    response = json.dumps(rates, indent=2, ensure_ascii=False)                    
                    await self.send_to_clients(f"Reply from PrivatBank to {ws.name}:")
                    await self.send_to_clients(response)
                    #await self.send_to_clients("Invalid exchange command format.")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
