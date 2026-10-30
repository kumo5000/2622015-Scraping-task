import csv
import time
from urllib.parse import urldefrag, urljoin, urlparse
from bs4 import BeautifulSoup
import requests

url = "https://www.musashino-u.ac.jp/"

# サーバーに負荷をかけないよう、通信前に1秒待機する
time.sleep(1)
res = requests.get(url, timeout=30)

print(f"ステータスコード：{res.status_code}")
res.raise_for_status()

# 取得したWebページのHTMLデータからタイトル情報を抽出する
html_soup = BeautifulSoup(res.content, "html.parser")
title = html_soup.title.string
print(f"タイトル：{title}")

# URLとページタイトルのセットを辞書に登録する
pages = {}
pages[url] = title
print(pages)

# 対象を限定するため、トップページのドメイン名を取得しておく
domain = urlparse(url).netloc

# ページ内にあるリンク付きのタグを全取得する
links = html_soup.find_all("a", href=True)
same_domain_urls = []

for link in links:
    # 相対パス表記のリンクを絶対パスの完全なURL形式に揃える
    next_url = urljoin(res.url, link["href"])

    # ページ内リンク用の末尾の＃をカットする
    next_url = urldefrag(next_url)[0]

    # URLの構成要素を解析する
    parsed_url = urlparse(next_url)

    # 外部サイトを除外し、同じドメインかつhttp/httpsの安全なURLのみを抽出する
    if parsed_url.scheme in ("http", "https") and parsed_url.netloc == domain:
        if next_url not in same_domain_urls:
            same_domain_urls.append(next_url)

for next_url in same_domain_urls:
    print(next_url)

print(f"同一ドメインの重複しないURL数：{len(same_domain_urls)}")

# 発見したURLリストを1つずつ取り出し、未訪問のページを巡回していく
index = 0
while index < len(same_domain_urls):
    page_url = same_domain_urls[index]
    index += 1
    # 既にデータを取得済みのページはスキップする
    if page_url in pages:
        continue

    time.sleep(1)
    try:
        res = requests.get(page_url, timeout=30)
        res.raise_for_status()
    except requests.RequestException as error:
        print(f"取得失敗：{page_url}：{error}")
        continue

    # リダイレクトによって対象外のドメインに飛ばされた場合は処理を中断する
    if urlparse(res.url).netloc != domain:
        continue

    # PDFや画像など、Webページ（HTML）以外のファイル形式は除外する
    content_type = res.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        continue

    html_soup = BeautifulSoup(res.content, "html.parser")

    # title要素が存在すればその文字列を取り出し、無ければ空文字を設定する
    if html_soup.title is not None:
        title = html_soup.title.get_text()
    else:
        title = ""

    pages[page_url] = title
    print(f"{page_url} → {title}")
    links = html_soup.find_all("a", href=True)

    for link in links:
        next_url = urljoin(res.url, link["href"])
        next_url = urldefrag(next_url)[0]
        parsed_url = urlparse(next_url)

        if parsed_url.scheme in ("http", "https") and parsed_url.netloc == domain:
            if next_url not in same_domain_urls:
                same_domain_urls.append(next_url)

print(f"タイトルを保存したページ数：{len(pages)}")
print(f"リンク先も調べた後のURL数：{len(same_domain_urls)}")

# 収集したURLとタイトルのデータをCSV形式で出力する
with open("sitemap.csv", "w", encoding="utf-8-sig", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["URL", "タイトル"])
    writer.writerows(pages.items())

print("sitemap.csvに保存しました")
#緒方 友哉　課題