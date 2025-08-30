import requests
from lxml import html
import csv
import time

# Kabutec 抓取函数
def fetch_kabutec_table(url, fourth_index=-1, fourth_threshold=None, split_second_column=True):
    res = requests.get(url)
    tree = html.fromstring(res.content)

    rows = tree.xpath('//tr')
    output = []

    for row in rows:
        cells = row.xpath('.//td//text()')
        cells = [c.strip() for c in cells if c.strip()]
        if not cells:
            continue

        # 第四列筛选
        fourth_value = None
        if fourth_index >= 0 and fourth_index < len(cells):
            try:
                fourth_value = float(cells[fourth_index].replace(',', ''))
            except:
                fourth_value = None
        pass_fourth = (fourth_index < 0 or fourth_value is None or
                       (fourth_threshold is not None and fourth_value < fourth_threshold))

        # 最后一列筛选（负值）
        try:
            last_value = float(cells[-1].replace(',', ''))
            pass_last = last_value < 0
        except:
            pass_last = True  # 如果不是数字也算通过

        if pass_fourth and pass_last:
            if split_second_column and len(cells) > 1 and ' / ' in cells[1]:
                parts = cells[1].split(' / ')
                cells[1] = parts[0].strip()  # 股票代码
                cells.insert(2, parts[1].strip())  # 公司名
            output.append(cells)
    return output

# Minkabu 判断抓取函数
def fetch_minkabu_judgment(stock_code):
    url = f'https://s.minkabu.jp/stock/{stock_code}/analyst_consensus'
    try:
        res = requests.get(url)
        tree = html.fromstring(res.content)
        # XPath：判断
        judgment = tree.xpath("//*[@id='contents']/div[2]/div[3]/div/div[1]/div[1]/div/div[1]/a/text()")
        if judgment:
            return judgment[0].strip()
        else:
            return 'N/A'
    except:
        return 'N/A'

# 主函数
def main():
    csv_file = 'kabutec_stocks.csv'
    all_data = []

    # 每类数据的 URL 和名称
    data_sources = [
        ('RSI', "https://www.kabutec.jp/contents/compare/com.php?col1=20&scol1=0&col2=2&scol2=0&col3=3&scol3=0", 3, 20),
        ('200日均线', "https://www.kabutec.jp/contents/compare/com.php?col1=10&scol1=0&col2=2&scol2=0&col3=3&scol3=0&market=0", -1, None),
        ('MACD', "https://www.kabutec.jp/contents/compare/com.php?col1=14&scol1=0&col2=2&scol2=0&col3=3&scol3=0", -1, None),
        ('配当', "https://www.kabutec.jp/contents/compare/com.php?col1=28&scol1=1&col2=2&scol2=0&col3=3&scol3=0", -1, None),
    ]

    for source_name, url, fourth_index, fourth_threshold in data_sources:
        print(f"Fetching {source_name} ...")
        rows = fetch_kabutec_table(url, fourth_index, fourth_threshold)
        for row in rows:
            stock_code = row[1] if len(row) > 1 else 'N/A'
            company_name = row[2] if len(row) > 2 else 'N/A'
            judgment = fetch_minkabu_judgment(stock_code)
            time.sleep(0.5)  # 避免访问过快
            # 不过滤 N/A，全部写入
            all_data.append([stock_code, company_name, judgment, source_name])

    # 写入 CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 表头
        writer.writerow(['股票代码', '公司名', '判断', '数据来源'])
        writer.writerows(all_data)

    print(f"完成，数据已写入 {csv_file}.")

if __name__ == '__main__':
    main()
