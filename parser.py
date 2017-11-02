# This Python file uses the following encoding: utf-8

import logging
import re
from random import randint

import requests
from bs4 import BeautifulSoup
import html2text
import unicodecsv as csv

logging.getLogger().setLevel(logging.INFO)


def parse_rozetka_printers(printer_n=0):
    url = 'https://rozetka.com.ua/printers-mfu/c80007/filter/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html5lib")
    page_n = int(soup.select_one('ul[name="paginator"]').find_all("li")[-1].a.text)

    printers = []
    for i in range(page_n):
        url = 'https://rozetka.com.ua/printers-mfu/c80007/filter/page=%d' % i
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html5lib")

        a_list = soup.select('.g-i-tile-i-title > a')
        href_list = [a['href'] for a in a_list]

        for href in href_list:
            r = requests.get(href + 'characteristics/')
            soup = BeautifulSoup(r.text, "html5lib")

            # Pages per minute
            text = soup.find(text="Скорость печати")
            if text is None:
                continue
            ppm_text = text.parent.parent.parent.find("span").text
            n = ppm_text.find(u"стр")
            ppm = float()
            if n != -1:
                try:
                    ppm = float(re.findall(r'[0-9,\.]+', ppm_text[0:n])[-1])
                except:
                    continue
            else:
                n = ppm_text.find(u"изобр")
                if n != -1:
                    try:
                        ppm = float(re.findall(r'[0-9,\.]+', ppm_text[0:n])[-1])
                    except:
                        continue
                else:
                    n = ppm_text.find(u"лист")
                    if n != -1:
                        try:
                            ppm = float(re.findall(r'[0-9,\.]+', ppm_text[0:n])[-1])
                        except:
                            continue
                    else:
                        continue

            # Printing technology
            text = soup.find(text="Технология печати")
            if text is None:
                continue
            pt = text.parent.parent.parent.span.a.text

            # Function type
            text = soup.find(text="Тип устройства")
            if text is None:
                continue
            ft = text.parent.parent.parent.span.a.text

            # Print size
            text = soup.find(text="Формат и плотность бумаги")
            if text is None:
                continue
            ps_text = text.parent.parent.parent.span.text
            ps = ""
            if ps_text.find(u"A4") != -1:
                ps = "A4"
            if ps_text.find(u"A3") != -1:
                ps = "A3"
            if ps_text.find(u"A3+") != -1:
                ps = "A2"
            if ps_text.find(u"A1") != -1:
                ps = "A1"
            if ps_text.find(u"A0") != -1:
                ps = "A0"
            if not ps:
                continue

            # Print resolution
            text = soup.find(text="Максимальное разрешение печати")
            if text is None:
                continue
            res_text = text.parent.parent.parent.span.text
            res_ar = re.findall(r'\d+', res_text)

            # Weight
            text = soup.find(text="Вес (кг)")
            weight = None
            if text is not None:
                weight_text = text.parent.parent.parent.span.text
                weight = float(re.findall(r'[0-9,\.]+', weight_text)[0])

            # Size
            text = soup.find(text="Размеры (Д х Ш х В), мм")
            size = ""
            if text is not None:
                size_text = text.parent.parent.parent.span.text
                size = re.findall(r'[0-9,\.-]+ . [0-9,\.-]+ . [0-9,\.-]+', size_text)[0]

            # Additional info
            additional_info = ""
            text = soup.find(text="Дополнительно")
            if text is not None:
                additional_info_html = text.parent.parent.parent.span
                additional_info = html2text.html2text(unicode(additional_info_html))

            # страница "Всё о товаре"
            r = requests.get(href)
            soup = BeautifulSoup(r.text, "html5lib")

            # Price
            text = soup.select_one('meta[itemprop="price"]')
            price = ""
            if text is None:
                continue
            price = text["content"]

            # Name
            name = soup.select_one('h1[class=detail-title]').string.split("+", 1)[0]

            # Brand
            brand = " ".join(soup.select('span[class=breadcrumbs-title]')[-1].string.split()[1:])


            # Description
            description = ""
            description_html = soup.find(id='short_text')
            if description_html is not None:
                description = html2text.html2text(unicode(description_html))

            printers.append({
                "Name": name,
                "Description": description,
                "PagePerMinute": ppm,
                "Brand": brand,
                "PrintingTechnology": pt,
                "FunctionType": ft,
                "PrintSize": ps,
                "PrintResolutionX": int(res_ar[0]),
                "PrintResolutionY": int(res_ar[1]),
                "Size": size,
                "Weight": weight,
                "AdditionalInfo": additional_info,
                "Amount": randint(1, 20),
                "Price": price
            })

            prnt_len = len(printers)
            logging.info("\n" + str(prnt_len) + ': ' + printers[prnt_len-1]["Name"])
            if printer_n and prnt_len == printer_n:
                break
        if printer_n and len(printers) == printer_n:
            break

    keys = printers[0].keys()
    with open('printers%d.csv' % len(printers), 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(printers)


parse_rozetka_printers()