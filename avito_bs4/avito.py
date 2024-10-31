from __future__ import annotations

import time
from typing import Any

import logging
from functools import reduce
from operator import iconcat
from bs4 import BeautifulSoup

from avito_scraper.proxy import get_proxy
from avito_scraper import base, database, settings


CAPCHA = 'Доступ ограничен: проблема с IP'
INITIAL_DATA = 'window.__initialData__ = '


def get_pages(url):
    page_urls = []

    proxy = get_proxy()
    response = base.get_response(url, proxy)

    # Получаем количество страниц пагинации
    page_count = base.get_page_count(response)

    for page in range(page_count):
        page_url = f"{url}&p={page + 1}"
        logging.info(f"Текущая страница: {page_url}")
        page_urls.append(page_url)

    return page_urls


def get_products(url: str):
    proxy = get_proxy()
    soup = BeautifulSoup(base.get_response(url, proxy).text, 'html.parser')
    products = soup.select('[data-marker="item"]')

    items = []
    for product in products:
        if item_url := product.select('[itemprop="url"]')[0].attrs['href']:
            item_url = f"https://www.avito.ru{item_url}"
        else:
            logging.info("Нет product")
            continue

        logging.info(item_url)

        name = product.select('[class^="iva-item-title"]')[0].text
        product_link = name.attrs['href']
        article = product_link.split('_')[-1]

        # Получаем значение продвижения (promotion). Если его нет, то возвращаем 0.
        # promotion = product.select('[itemprop="url"]') if 0 else 0
        # number_of_days_promotion = product.select('[itemprop="url"]') if 0 else 0
        # promotion_type = product.select('[itemprop="url"]') if 0 else 0
        price = product.select('meta[itempror="price"]')[0].attrs['content']
        availability = product.select('[class^="iva-item-badgeBarStep"]')

        # if promotion and promotion != "Продвинуто":
        #     promotion = 0

        #Заходим на страницу чтобы получит атрибуты
        proxy = get_proxy()
        product_data = BeautifulSoup(base.get_response(url, proxy).text, 'html.parser')
        product_attrs = product_data.select('[data-marker="item-view/item-params"]')
        logging.info(product_attrs)

        seller = product.select('[itemprop="url"]')
        region = product.select('[itemprop="url"]')
        advertisement_date = product.select('[itemprop="url"]')
        brand = product.select('[itemprop="url"]')
        model = product.select('[itemprop="url"]')
        body_type = product.select('[itemprop="url"]')
        year_of_issue = product.select('[itemprop="url"]')
        wheel_formula = product.select('[itemprop="url"]')
        condition = product.select('[itemprop="url"]')
        company_individual_vendor = product.select('[itemprop="url"]')


        attrs = {
            "price": price, # Цена
            "availability": availability, # Доступность
            "seller": seller,  # Продавец
            "region": region, # Регион
            # "promotion": promotion, # Продвижение
            # "number_of_days_promotion": number_of_days_promotion, # Количество дней (продвижение)
            # "promotion_type": promotion_type, # Тип продвижения
            "advertisement_date": advertisement_date, # Дата объявления
            "brand": brand, # Марка
            "model": model, # Модель
            "body_type": body_type, # Тип кузова
            "year_of_issue": year_of_issue, # Год выпуска
            "wheel_formula": wheel_formula, # Колесная формула
            "condition": condition, # Состояние
            "company_individual_vendor": company_individual_vendor, # Компания / частное лицо
        }

        item = database.Item(
            name=name,
            article=article,
            url=product_link,
            attrs=attrs,
        )
        logging.info(item)
        items.append(item)

    return items


def parse() -> set[Any]:
    """Запускает парсинг avito."""
    items = []
    for url in settings.AVITO_URLS:
        logging.info(f"Запускаю страницу {url}")
        pages = get_pages(url)
        time.sleep(5)
        for page in pages:
            result = get_products(page)
            items.append(result)

    items = set(reduce(iconcat, items, []))
    logging.info(f"Avito: всего товаров: {len(items)}")
    if items:
        database.insert_items(items)
    else:
        logging.warning("Нет товаров для добавления в базу данных.")

    return items
