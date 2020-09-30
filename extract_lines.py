import json

from bs4 import BeautifulSoup


def extract_data(html):
    soup = BeautifulSoup(html)
    line_divs = soup.find_all("div", class_="clearfix")
    line_dict = {}
    for div in line_divs:
        line_items = div.find_all("a")
        lines = []
        for item in line_items:
            lines.append(item.text.strip())
        line_dict[div.attrs["line-type"]] = lines
    return line_dict


if __name__ == "__main__":
    f = open("lines.html")
    lines = extract_data(f.read())
    f.close()
    f = open("lines.json", "w+")
    f.write(json.dumps(lines))
    f.close()
