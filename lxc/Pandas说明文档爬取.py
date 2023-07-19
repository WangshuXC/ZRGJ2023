# 导入所需模块
import requests
import lxml
from bs4 import BeautifulSoup
import time
import os
import random
import csv
from tqdm import tqdm
from openpyxl import Workbook
from datetime import datetime
import threading

user_agents = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]

request_headers = {
    "User-agent": random.choice(user_agents),
    "Connection": "keep-alive",
}

(
    functions_prename_list,
    functions_name_list,
    parameters_list,
    returns_list,
    urls_list,
    threads,
) = ([], [], [], [], [], [])

pbar = tqdm(
    desc="具体进度",
    total=4166,
    colour="red",
    mininterval=3.0,
    maxinterval=10.0,
)


# 运用workbook库来进行excel文件形式的数据保存，便于数据分析以及优化
def write_dict_to_excel(data_dict, filename):
    # 获取.py文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 生成完整的文件路径
    file_path = os.path.join(
        current_dir,
        datetime.now().strftime("%Y-%m-%d %H-%M") + " " + filename.replace(":", "_"),
    )
    # 创建一个新的Excel工作簿
    workbook = Workbook()
    # 获取活动的工作表
    worksheet = workbook.active
    # 写入表头
    worksheet.append(list(data_dict.keys()))
    # 写入数据
    for row in zip(*data_dict.values()):
        worksheet.append(row)
    # 保存文件
    workbook.save(file_path)


# csv的数据保存，便于后续进行数据库数据导入
def write_data_to_csv(data, filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(
        current_dir, datetime.now().strftime("%Y-%m-%d %H-%M") + " " + filename
    )
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["方法名称1", "方法名称2", "方法参数", "返回值类型", "链接"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in zip(*data.values()):
            writer.writerow(dict(zip(fieldnames, row)))


def spider_get_urls(url):
    web_data = requests.get(url=url, headers=request_headers)
    status_code = web_data.status_code
    urls = []
    if status_code == 200:
        html_text = web_data.text
        soup_document = BeautifulSoup(html_text, "lxml")
        divs_all = soup_document.select("li.toctree-l1")
        for div in divs_all:
            module_link = div.find(class_="reference internal").get("href")
            urls.append(url + module_link)
        return urls
    # 得到的urls还需要人工二次筛选，已在下方给出筛选过后的urls


# 用于获取具体页面的url
def spider_big(url):
    web_data = requests.get(url=url, headers=request_headers)
    status_code = web_data.status_code
    if status_code == 200:
        html_text = web_data.text
        soup_document = BeautifulSoup(html_text, "lxml")
        divs_all = soup_document.select("ul li.toctree-l2")

        for div in divs_all:
            function_link_element = div.find(class_="reference internal").get("href")
            function_link = (
                "https://pandas.pydata.org/pandas-docs/stable/reference/"
                + str(function_link_element)
            )
            # print(url)
            # print(function_link)

            if judge(function_link):
                continue
            else:
                spider_small(function_link)


# 用于抓取具体页面上的方法名、参数以及返回值
def spider_small(function_link):
    web_data = requests.get(url=function_link, headers=request_headers)
    status_code = web_data.status_code
    if status_code == 200:
        html_text = web_data.text
        soup_document = BeautifulSoup(html_text, "lxml")

        divs_all = soup_document.select("dt.sig.sig-object.py")

        selected_elements1 = divs_all[0].select("span.sig-prename.descclassname")
        function_prename = (
            selected_elements1[0].get_text() if selected_elements1 else "None"
        )

        selected_elements2 = divs_all[0].select("span.sig-name.descname")
        function_name = (
            selected_elements2[0].get_text() if selected_elements2 else "None"
        )

        parameter = divs_all[0].get_text()
        start = parameter.find("(")
        end = parameter.rfind(")")
        parameter = parameter[start : end + 1]

        # 由于pandas官方文档格式不统一，故需要多重选择用于筛选正确的返回值
        return_ = ""
        if function_name.startswith("is_"):
            return_ = "boolean"
        else:
            if soup_document.select("dt.field-even"):
                if soup_document.select("dt.field-even")[0].get_text() == "Returns":
                    return_ = soup_document.select("dd.field-even dl dt")[0].get_text()
                    if return_.startswith("out"):
                        return_ = return_[3:]

                else:
                    if soup_document.select("dl.py.attribute dd p"):
                        return_ = get_word_after_return(
                            soup_document.select("dl.py.attribute dd p")[0].get_text()
                        )

            elif soup_document.select("dl.field-list.simple dt.field-odd"):
                if (
                    soup_document.select("dl.field-list.simple dt.field-odd")[
                        0
                    ].get_text()
                    == "Returns"
                ):
                    return_ = soup_document.select(
                        "dl.field-list.simple dd.field-odd dl dt"
                    )[0].get_text()
                    if return_.startswith("out"):
                        return_ = return_[3:]

                else:
                    if soup_document.select("dl.py.attribute dd p"):
                        return_ = get_word_after_return(
                            soup_document.select("dl.py.attribute dd p")[0].get_text()
                        )

        # 将数据转移到列表中，方便后续写入文件
        functions_prename_list.append(function_prename)
        functions_name_list.append(function_name)
        parameters_list.append(parameter)
        returns_list.append(return_)
        urls_list.append(function_link)
        pbar.update()


def judge(function_link):
    web_data = requests.get(url=function_link, headers=request_headers)
    status_code = web_data.status_code
    if status_code == 200:
        html_text = web_data.text
        soup_document = BeautifulSoup(html_text, "lxml")
        divs_all = soup_document.select("ul li.toctree-l4")
        for div in divs_all:
            if any(div):
                div_s_all = div.select("li.toctree-l4")
                for div_ in div_s_all:
                    function_link_element = div_.find(class_="reference internal").get(
                        "href"
                    )
                    if function_link_element.startswith("generated/"):
                        function_link_element = function_link_element[
                            len("generated/") :
                        ]
                    function_link = (
                        "https://numpy.org/devdocs/reference/generated/"
                        + str(function_link_element)
                    )

                    spider_small(function_link)
                return 1
        return 0


# 用于得到返回值
def get_word_after_return(s):
    if s.startswith("Return a "):
        return s.split(" ")[2]
    elif s.startswith("Return an "):
        return s.split(" ")[2]
    else:
        return None


if __name__ == "__main__":
    # url = "https://pandas.pydata.org/pandas-docs/stable/reference/"
    # 得到urls
    # urls = spider_get_urls(url)
    urls = [
        "https://pandas.pydata.org/pandas-docs/stable/reference/io.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/general_functions.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/series.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/frame.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/arrays.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/indexing.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/offset_frequency.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/window.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/groupby.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/resampling.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/style.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/plotting.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/options.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/extensions.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/testing.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/io.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/general_functions.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/series.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/frame.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/arrays.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/indexing.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/offset_frequency.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/window.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/groupby.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/resampling.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/style.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/plotting.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/options.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/extensions.html",
        "https://pandas.pydata.org/pandas-docs/stable/reference/testing.html",
    ]

    for url in urls:
        t = threading.Thread(target=spider_big, args=(url,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 关闭进度条
    pbar.close()

    data = {
        "方法名称1": functions_prename_list,
        "方法名称2": functions_name_list,
        "方法参数": parameters_list,
        "返回值类型": returns_list,
        "链接": urls_list,
    }

    write_data_to_csv(data, "pandas说明文档.csv")
    write_dict_to_excel(data, "pandas说明文档.xlsx")
    print("爬取完毕！")
