import time
import re
import argparse
import random

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt


def get_headers(page, cookie):
    headers = {
        'authority': 'qd.anjuke.com',
        'method': 'GET',
        'path': '/sale/p{}/'.format(page),
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-max-age=0',
        'cookie': cookie,
        'pragma': 'no-cache',
        'referer': 'https://qd.anjuke.com/sale/p{}/'.format((page-1) if page > 1 else page),
        "sec-fetch-dest": "document",
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }
    return headers


def get_html_by_page(page, cookie):
    headers = get_headers(page, cookie)
    url = 'https://qd.anjuke.com/sale/p{}/'.format(page)
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print('页面不存在！')
        return None
    return res.text


def extract_data_from_html(html):
    soup = BeautifulSoup(html)
    if soup.find("div", class_="error-page") is not None:
        if "系统检测到" in soup.find("div", class_="error-page").div.text:
            print("命中反爬策略...")
            return None
    list_content = soup.find(id="houselist-mod-new")
    if not list_content:
        return None
    items = list_content.find_all('li', class_='list-item')
    if len(items) == 0:
        return None
    page_data = []
    for item in items:
        # page_data += extract_data(item)
        try:
            page_data.append(extract_data(item))
        except IndexError:
            continue
    # return [extract_data(item) for item in items]
    return page_data


def extract_data(item):
    name = item.find_all('a')[0].text.strip()
    details = item.find_all("div", class_="details-item")
    details_items = details[0].find_all("span")
    house_type = details_items[0].text.strip()
    area = details_items[1].text.strip()
    floor = details_items[2].text.strip()
    build_year = ""
    if len(details_items) > 3:
        build_year = details_items[3].text.strip()
    address = BeautifulSoup(details[1].find("span").text).prettify(formatter=lambda s: s.replace(u'\xa0', ' ')).strip()
    address = re.sub(r"\s+", " ", address)
    price_item = item.find("div", class_="pro-price")
    price = price_item.find_all("span")[0].text.strip()
    unit_price = price_item.find_all("span")[1].text.strip()
    # if item.strong is not None:
    #     price = item.strong.text.strip()
    # else:
    #     price = None
    # finish_date = item.p.text.strip().split('：')[1]
    # latitude, longitude = [d.split('=')[1] for d in item.find_all('a')[3].attrs['href'].split('#')[1].split('&')[:2]]
    return name, address, price, unit_price, house_type, area, floor, build_year


def crawl_all_page(cookie, latency, debug=False):
    page_num = 1
    data_raw = []
    # while True:
    for page in range(1, 61):
        try:
            html = get_html_by_page(page, cookie)
            data_page = extract_data_from_html(html)
            if not data_page:
                break
            data_raw += data_page
            print('crawling {}th page ...'.format(page))
            page_num += 1
            if debug:
                break
            time.sleep(latency + random.random()*5)
        except Exception as e:
            print('maybe cookie expired!')
            print("error=%s" % e)
            break
    print('crawl {} pages in total.'.format(page_num-1))
    return data_raw


def create_df(data):
    columns = ['name', 'address', 'price', "unit_price", "house_type", "area", "floor", "build_year"]
    return pd.DataFrame(data, columns=columns)


def clean_data(df):
    df.dropna(subset=['price'], inplace=True)
    # df = df.astype({'price': 'float64', 'latitude': 'float64', 'longitude': 'float64'})
    return df


def visual(df):
    fig, ax = plt.subplots()
    df.plot(y='price', ax=ax, bins=20, kind='hist', label='房价频率直方图', legend=False)
    ax.set_title('房价分布直方图')
    ax.set_xlabel('房价')
    ax.set_ylabel('频率')
    plt.grid()
    plt.show()


def run(args):
    data = crawl_all_page(args.cookie, args.latency, args.debug)
    df = create_df(data)
    df = clean_data(df)
    # visual(df)
    df.sort_values('price', inplace=True)
    df.reset_index(drop=True, inplace=True)
    #  保存 csv 文件
    filename = time.strftime("%Y-%m-%d", time.localtime())
    csv_file = filename + '.csv'
    df.to_csv(csv_file, index=False)


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cookie', type=str, help='cookie.')
    parser.add_argument("-l", "--latency", type=float, help="latency between two request", default=1.0)
    parser.add_argument("-d", dest="debug", action="store_true")
    parser.set_defaults(debug=False)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main_args = get_cli_args()
    run(main_args)
