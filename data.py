import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide")

class PriceComparisonScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.scrapers = {
            "Feebee": self.scrape_feebee,
            "Pchome": self.scrape_pchome,
            "Anazon": self.scrape_amazon,
            "E-bay": self.scrape_ebay
        }

    def scrape_feebee(self, keyword, num_pages=1):
        base_url = "https://feebee.com.tw/s/"
        all_products = []

        for page in range(1, num_pages + 1):
            params = {"q": keyword, "page": page}
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                products = soup.find("ol")
                
                try:
                    for product in products.find_all("li"):
                        title_element = product["data-title"]
                        price_element = product["data-price"]
                        link_element = product["data-url"]
                        source_element = product["data-store"]
                
                        if title_element and price_element and link_element:
                            title = title_element
                            price = price_element
                            link = link_element
                            source = source_element
                    
                            all_products.append({
                                "title": title,
                                "price": price,
                                "link": link,
                                "source": source
                            })

                except:
                    pass
                
                time.sleep(random.uniform(1, 3))
            except requests.RequestException as e:
                st.write(f"Feebee 錯誤發生: {e}")
                break

        return all_products

    def scrape_pchome(self, keyword, num_pages=1):
        base_url = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
        all_products = []

        for page in range(1, num_pages + 1):
            params = {"q": keyword, "page": page, "sort": "sale/dc"}
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                for product in data.get("prods", []):
                    title = product.get("name")
                    price = product.get("price")
                    link = f"https://24h.pchome.com.tw/prod/{product.get('Id')}"
                    
                    all_products.append({"title": title, "price": price, "link": link, "source": "Pchome"})
                
                time.sleep(random.uniform(1, 3))
            except requests.RequestException as e:
                st.write(f"Pchome 錯誤發生: {e}")
                break

        return all_products

    def scrape_amazon(self, keyword, num_pages=1):
        base_url = "https://www.amazon.com/s"
    
        all_products = []

        for page in range(1, num_pages + 1):
            params = {
                "k": keyword,
                "page": page
            }
            
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                products = soup.find_all("div", {"data-component-type": "s-search-result"})
                
                for product in products:
                    title_element = product.find("h2", class_="a-size-mini")
                    price_element = product.find("span", class_="a-price-whole")
                    link_element = product.find("a", class_="a-link-normal s-no-outline")
                    
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price = price_element.text.strip()
                        link = "https://www.amazon.com" + link_element.get("href")
                        
                        all_products.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "source": "Amazon"
                        })
                
                # 隨機延遲,避免被檢測為機器人
                time.sleep(random.uniform(1, 3))
                
            except requests.RequestException as e:
                st.write(f"Error occurred: {e}")
                break
        
        return all_products

    def scrape_ebay(self, keyword, num_pages=1):
        base_url = "https://www.ebay.com/sch/i.html"
        all_products = []

        for page in range(1, num_pages + 1):
            params = {
                "_nkw": keyword,
                "_pgn": page
            }
            
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                products = soup.find_all("div", class_="s-item__info clearfix")
                
                for product in products:
                    title_element = product.find("div", class_="s-item__title")
                    price_element = product.find("span", class_="s-item__price")
                    link_element = product.find("a", class_="s-item__link")
                    
                    if title_element and price_element and link_element:
                        title = title_element.text.strip()
                        price = price_element.text.strip()
                        link = link_element["href"]
                        
                        all_products.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "source": "E-bay"
                        })
                
                # 隨機延遲,避免被檢測為機器人
                time.sleep(random.uniform(1, 3))
                
            except requests.RequestException as e:
                st.write(f"Error occurred: {e}")
                break

        return all_products

    def scrape_all(self, keyword, num_pages=1):
        all_results = []
        with ThreadPoolExecutor(max_workers=len(self.scrapers)) as executor:
            future_to_scraper = {executor.submit(scraper, keyword, num_pages): name 
                                 for name, scraper in self.scrapers.items()}
            for future in as_completed(future_to_scraper):
                name = future_to_scraper[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as exc:
                    st.write(f'{name} 產生了一個異常: {exc}')
        return all_results

# 使用示例

scraper = PriceComparisonScraper()
keyword = st.text_input("Searching")
results = scraper.scrape_all(keyword, num_pages=2)

# 按價格排序結果
#sorted_results = sorted(results, key=lambda x: float(x['price']))

if keyword:
    df = pd.DataFrame(results, columns=("title", "price", "link", "source"))
    st.dataframe(df, use_container_width=True, column_config={
        "website": st.column_config.LinkColumn()
    })
