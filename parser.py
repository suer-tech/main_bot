from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

def get_price(name, url, xpath):
    url = "https://ru.investing.com/currencies/usd-rub"

    driver.get(url)
    price = driver.find_element('xpath', '//span[@class="text-2xl"]').text
    print(price)

url_gld = "https://ru.investing.com/commodities/gold"

driver.get(url_gld)
price_gld = driver.find_element('xpath', '//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[3]/div/div[1]/div[1]/div[1]').text
print(price_gld)

currencies = [{
    name: 'usd',
    url: "https://ru.investing.com/currencies/usd-rub",
    xpath: '//span[@class="text-2xl"]',
},
{
    name: 'cny',
    url: "https://ru.investing.com/currencies/cny-rub",
    xpath: '//span[@class="text-2xl"]',
},
{
    name: 'eur',
    url: "https://ru.investing.com/currencies/eur-rub",
    xpath: '//span[@class="text-2xl"]',
},
]

comodities = [{
    name: 'usd',
    url: "https://ru.investing.com/currencies/usd-rub",
    xpath: '//span[@class="text-2xl"]',
},
{
    name: 'cny',
    url: "https://ru.investing.com/currencies/cny-rub",
    xpath: '//span[@class="text-2xl"]',
},
{
    name: 'eur',
    url: "https://ru.investing.com/currencies/eur-rub",
    xpath: '//span[@class="text-2xl"]',
},
]