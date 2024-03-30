# WEBHW5

Home work for 5 module
Create console app that will return exchange rate of EUR and USD for serveral last days from PrivatBank arhive using it's API
(for example, https://api.privatbank.ua/p24api/exchange_rates?json&date=01.12.2022).
Set limit to let user know currency exchange rate not more than for 10 last days.
For requests to API use Aiohttp client.
Adhere SOLID principles during implementation of the task.
Handle network errors properly

Example call:
py .\main.py 2

Result:
[
{
'03.11.2022': {
'EUR': {
'sale': 39.4,
'purchase': 38.4
},
'USD': {
'sale': 39.9,
'purchase': 39.4
}
}
},
{
'02.11.2022': {
'EUR': {
'sale': 39.4,
'purchase': 38.4
},
'USD': {
'sale': 39.9,
'purchase': 39.4
}
}
}
]

Additional Part

- Add possibility to pass additional currencies via parameters
- Add to the chat on sockets ability to write command exchange that will show users current exchange rate in a text format
- Extend added command exchange, to have the ability to get exchange rate in a chat for the last several days. For example, exchange 2
- with the help of packages auifile and aiopath add logging to the file, when exchange was called in a chat
