import asyncio
import aiohttp
import pprint

class ExchangeRateFetcher:
    def __init__(self):
        self.base_url = 'https://api.privatbank.ua/p24api/exchange_rates'

    async def fetch_exchange_rate(self, session, date):
        url = f"{self.base_url}?date={date}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

    async def get_exchange_rates(self, dates):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_exchange_rate(session, date) for date in dates]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

def format_exchange_rate_data(data):
    formatted_data = []
    for entry in data:
        if entry is not None:
            rates = entry['exchangeRate']
            formatted_entry = {entry['date']: {'EUR': {}, 'USD': {}}}
            for rate in rates:
                if rate['currency'] == 'EUR':
                    formatted_entry[entry['date']]['EUR']['sale'] = rate.get('saleRate', rate['saleRateNB'])
                    formatted_entry[entry['date']]['EUR']['purchase'] = rate.get('purchaseRate', rate['purchaseRateNB'])
                elif rate['currency'] == 'USD':
                    formatted_entry[entry['date']]['USD']['sale'] = rate.get('saleRate', rate['saleRateNB'])
                    formatted_entry[entry['date']]['USD']['purchase'] = rate.get('purchaseRate', rate['purchaseRateNB'])
            formatted_data.append(formatted_entry)
    return formatted_data

async def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py <number_of_days>")
        return

    try:
        num_days = int(sys.argv[1])
        if (num_days > 10) or (num_days < 1):
            print("Number of days should not exceed 10 and should be > 0.")
            return
    except ValueError:
        print("Invalid input. Please provide a valid number of days.")
        return

    dates = [(datetime.date.today() - datetime.timedelta(days=i)).strftime("%d.%m.%Y") for i in range(num_days)]
    exchange_rate_fetcher = ExchangeRateFetcher()
    exchange_rate_data = await exchange_rate_fetcher.get_exchange_rates(dates)
    formatted_data = format_exchange_rate_data(exchange_rate_data)
    #print(formatted_data)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(formatted_data)

if __name__ == "__main__":
    import datetime
    asyncio.run(main())