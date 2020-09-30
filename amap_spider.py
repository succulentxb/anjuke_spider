import time
import argparse
import random
import logging
import json

import requests


logging.basicConfig(level=logging.INFO)


def get_headers(cna):
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "amapuuid": "d94876a6-950e-40dd-b4bd-eab0f18d4929",
        "Connection": "keep-alive",
        "Cookie": "passport_login=MzM3Mzc2MzQ5LGFtYXBBc0N0UWNncmQsb3B4MnYzc3lsN2FjczQybWY1aG"
                  "Q2dm9jN2RuYXVwYXMsMTYwMTAwNjQwOCxPREJsWVRJeFpUTXlOekF4WkRZM01UQXlZVGRrT0R"
                  "jMU1qVTVZMll3WldFPQ%3D%3D; UM_distinctid=174d7c64ebc5e9-09a906184b4793-31"
                  "697304-384000-174d7c64ebd1f4; cna=Ksh9FH3zCnECAbSgl6Qd6b9m; _uab_collina="
                  "160134793350968452369346; xlly_s=1; CNZZDATA1255626299=285836182-16013478"
                  "47-https%253A%252F%252Fwww.google.com%252F%7C1601449885; x5sec=7b22617365"
                  "727665723b32223a223662356234353432613638633835333537613866316637346331353"
                  "238303736434d62363050734645504b50714f535869764f446e77453d227d; x-csrf-tok"
                  "en=db28ec25248599b8c18ddd203c0c1f79; tfstk=cUmFBVtMWuc1qerWkkZPVEUF7H7dZK"
                  "uIPNy0-4AbI2JPFSahiV18IxRQ_7Vvjyf..; l=eBMn8--cO1Xlq76jBOfZ-urza77OlIRbhu"
                  "PzaNbMiOCP9v5M5Ek1WZz81-LHCnhVHs_yJ3ovGkWTBXTp9PR8MMR-lKrgcM4E3dC..; isg="
                  "BKioAX04Yz-j-E-9s5SRUVETeZC60Qzbs9StKGLZlSMWvUknC-EuaxT7tFVN98Sz",
        "Host": "gaode.com",
        "Referer": "https://gaode.com/search?query=1%E8%B7%AF&"
                   "city=370200&geoobj=120.412456%7C36.284603%7"
                   "C120.431453%7C36.309131&zoom=15.12",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 "
                      "Safari/537.36",
        "x-csrf-token": "c0dd8a12fe48dd293290e31a37bb46d6",
        "X-Requested-With": "XMLHttpRequest"
    }


def get_params(keyword):
    return {
        "query_type": "TQUERY",
        "pagesize": 20,
        "pagenum": 1,
        "qii": "true",
        "cluster_state": 5,
        "need_utd": "true",
        "utd_sceneid": 1000,
        "div": "PC1000",
        "addr_poi_merge": "true",
        "is_classify": "true",
        "zoom": 14.1,
        "city": 370200,
        "keywords": keyword
    }


def request_amap(keyword, cna):
    url = "https://gaode.com/service/poiInfo"
    params = get_params(keyword)
    headers = get_headers(cna)
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        logging.info("[request_amap] failed request amap poiInfo, status=%s" % resp.status_code)
        return None
    try:
        resp_data = json.loads(resp.content)
        return resp_data
    except json.decoder.JSONDecodeError:
        logging.info("[request_amap] failed request amap poiInfo, resp=%s" % resp.content)
        return None


def crawl_line(line, cna):
    logging.info("[crawl_line] start crawl info for line=%s" % line)
    poi_info = request_amap(line, cna)
    if poi_info is None or poi_info.get("status") != "1" or not poi_info.get("data"):
        logging.info("[crawl_line] failed crawl info for line=%s, resp=%s" % (line, poi_info))
        return None
    poi_info = poi_info.get("data")
    bus_lines = poi_info.get("busline_list")
    if bus_lines is None or len(bus_lines) < 1:
        logging.info("[crawl_line] bus line info not found for line=%s, resp=%s" % (line, poi_info))
        return None
    return bus_lines[0]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cna", type=str, help="cna in amap request cookie")
    parser.add_argument("-l", "--latency", type=float, help="latency between two request", default=1.0)
    return parser.parse_args()


if __name__ == "__main__":
    main_args = parse_args()
    f = open("lines_test.json")
    line_dict = json.loads(f.read())
    f.close()
    failed_line_dict = {}
    line_data_dict = {}
    for line_type, lines in line_dict.items():
        line_data_list = []
        failed_line_list = []
        for line_name in lines:
            line_data = crawl_line(line_name, main_args.cna)
            time.sleep(main_args.latency + random.random() * 5)
            if line_data is None:
                failed_line_list.append(line_name)
                continue
            line_data_list.append(line_data)
        line_data_dict[line_type] = line_data_list
        failed_line_dict[line_type] = failed_line_list
    f = open("lines_data.json", "w")
    f.write(json.dumps({
        "line_data": line_data_dict,
        "failed_lines": failed_line_dict
    }))
    f.close()
    logging.info("[main] done!")
