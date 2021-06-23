from requests_html import HTMLSession
import threading
import pandas as pd
import time


class SmartphoneScraper:
    def __init__(self):
        self.session = HTMLSession()
        self.output_ready = list()

    # ZWRACA WSZYSTKIE LINKI DO POSZCZEGOLNYCH PRODUKTOW
    # NA DANEJ STRONIE
    def request(self, URL):
        r = self.session.get(URL)
        r.html.render(sleep=1)
        products = r.html.find("#listing-container", first=True)
        return products.absolute_links

    def parse(self, product, params):
        if "#Opinie" not in product:
            r = self.session.get(product)
            title = r.html.find("h1.sc-1bker4h-4", first=True).text
            price = r.html.find("div.u7xnnm-0", first=True).text
            price_split = price.split("\n")

            try:
                rat = r.html.find("div.sc-1cbpuwv-3", first=True).text.split("/")
                rat_count = r.html.find("div.sc-1cbpuwv-5", first=True).text
                rating = f"{rat[0]} / {rat[1]}\n{rat_count}"
            except Exception:
                rating = "No rating"

            info = r.html.find("li.p7lf0n-1")
            specs = r.html.find("div.sc-13p5mv-2", first=True).text
            specs_split = specs.split("\n")

            try:
                ram = specs_split[(specs_split.index("Pamięć RAM")) + 1]
                battery = specs_split[(specs_split.index("Pojemność baterii")) + 1]
            except ValueError:
                ram = None
                battery = None

            parsed_info = dict()
            for i in info:
                split = i.text.split(":")
                parsed_info[split[0]] = split[1]

            # SPRAWDZ CZY PRODUKT JEST NA PROMOCJI
            if "Oszczędź" in price:
                discount = f"{price_split[-2]} --> {price_split[-1]}"
            else:
                discount = "No"

            # SPRAWDZ STATUS DOSTEPNOSCI DANEGO PRODUKTU
            try:
                availability = r.html.find("span.sc-1smss4h-5", first=True).text
            except Exception:
                availability = None

            stock = False if availability == "Powiadom o dostępności" else stock = True

            price_converted = int(price_split[-1].split(",")[0].replace(" ", ""))

            if parsed_info.get("System") == params.get("system") and price_converted <= params.get("price_under"):
                self.output_ready.append({
                    "Title": title, "Processor": parsed_info.get("Procesor"),
                    "Memory": parsed_info.get("Pamięć"), "Ram": ram, "Battery": battery,
                    "System": parsed_info.get("System"), "Price": price_split[-1],
                    "Discount": discount, "Stock": stock, "Rating": rating, "Link": product
                })

    # EKSPORTUJE PRODUKTY DO PLIKU CSV
    def output(self):
        filename = "Smartphones.csv"
        df = pd.DataFrame(self.output_ready)
        df.to_csv(filename, index=False)
        print(f"Exported data to {filename}.")


if __name__ == "__main__":

    scraper = SmartphoneScraper()
    # PARAMETRY WYSZUKIWANIA
    params = {
        "price_under": 1500,
        "system": "Android 11"
    }

    threads = list()
    for i in range(2):
        URL = f"https://www.x-kom.pl/g-4/c/1590-smartfony-i-telefony.html?page={i+1}"
        links = scraper.request(URL)
        print(f"Scraping page {i + 1}.")
        for link in links:
            t = threading.Thread(target=scraper.parse, args=(link, params))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

        threads = list()
        time.sleep(2)

    scraper.output()
