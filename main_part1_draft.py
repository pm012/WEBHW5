import asyncio
import aiohttp
from abc import ABC, abstractclassmethod, abstractmethod
import datetime

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

class ExchangeRatePrinter(ABC):
    @abstractmethod
    def format_exchange_rate_data(self, data):
        pass

    @abstractmethod
    def print_exchange_rate_data(self, formatted_data):
        pass

    @abstractmethod
    def check_currency_availability(self, data, currencies):
        pass

class DefaultExchangeRatePrinter(ExchangeRatePrinter):
    def format_exchange_rate_data(self, data):
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

    def print_exchange_rate_data(self, formatted_data):
        print(formatted_data)

    def check_currency_availability(self, data, currencies):
        available_currencies = set()
        for entry in data:
            if entry is not None:
                rates = entry['exchangeRate']
                for rate in rates:
                    currency = rate['currency']
                    if currency in currencies:
                        available_currencies.add(currency)
        return available_currencies

class ExtendedExchangeRatePrinter(DefaultExchangeRatePrinter):
    def format_exchange_rate_data(self, data):
        formatted_data = super().format_exchange_rate_data(data)
        for entry in formatted_data:
            for currency in list(entry[next(iter(entry))]):
                if currency not in ('EUR', 'USD'):
                    del entry[next(iter(entry))][currency]
        return formatted_data


async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <number_of_days> [currency1 currency2 ...]")
        return

    try:
        num_days = int(sys.argv[1])
        if num_days > 10:
            print("Number of days should not exceed 10.")
            return
    except ValueError:
        print("Invalid input. Please provide a valid number of days.")
        return

    currencies = sys.argv[2:] if len(sys.argv) > 2 else ['USD', 'EUR']

    dates = [(datetime.date.today() - datetime.timedelta(days=i)).strftime("%d.%m.%Y") for i in range(num_days)]
    exchange_rate_fetcher = ExchangeRateFetcher()
    exchange_rate_data = await exchange_rate_fetcher.get_exchange_rates(dates)

    printer = ExtendedExchangeRatePrinter() if 'AUD' in currencies else DefaultExchangeRatePrinter()
    formatted_data = printer.format_exchange_rate_data(exchange_rate_data)

    available_currencies = printer.check_currency_availability(exchange_rate_data, currencies)
    if len(available_currencies) != len(currencies):
        missing_currencies = set(currencies) - available_currencies
        print(f"Error: The following currencies are not available: {', '.join(missing_currencies)}")
        return

    printer.print_exchange_rate_data(formatted_data)

if __name__ == "__main__":
    asyncio.run(main())