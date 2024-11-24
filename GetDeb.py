############################################################
# Debianのdebファイルをから依存関係を含めてDLするヤツ
# 
# ■実行コマンド
# > python GetDeb.py  パッケージ名  コードネーム  アーキテクチャー
# 
# ■インストールコマンド＠Debian
# # dpkg -i *.deb
# 
############################################################


import requests
from bs4 import BeautifulSoup
import sys
import os
import shutil
import urllib.request

URL = 'https://packages.debian.org/'
downloaded_packages = set()  # ダウンロード済みパッケージを記録するセット

def get_package(package, package_name, suite, architecture):
    # パッケージが既にダウンロード済みの場合はスキップ
    if package_name in downloaded_packages:
        print(f"Package {package_name} already downloaded. Skipping.")
        return

    # パッケージを記録
    downloaded_packages.add(package_name)

    # パッケージのページ
    print(package_name)
    pkg_res = requests.get(f'{URL}{suite}/{package_name}')
    if pkg_res.status_code != 200:
        print(f"Error fetching the package page for {package_name}")
        return

    pkg_soup = BeautifulSoup(pkg_res.text, 'html.parser')
    pkg_list = pkg_soup.find('div', id='pdownload')  # DLリストの取得
    if pkg_list is not None:
        pkg_link = pkg_list.find(name='a', href=True, string=['all', str(architecture)])
        if not pkg_link:
            print(f"No matching download link found for {package_name}")
            return

        # DLページ
        DL_res = requests.get(f'{URL}{pkg_link["href"]}')
        DL_soup = BeautifulSoup(DL_res.text, 'html.parser')
        DL_link = DL_soup.find(name='a', href=True, string="ftp.jp.debian.org/debian")  # 理研指定
        if DL_link is None:
            print(f"No Riken download link found for {package_name}")
            return

        print("\tlink\t" + f"{DL_link['href'].split('/')[-1]}")
        FileName = f"./{package}/{DL_link['href'].split('/')[-1]}"  # ファイル名
        if not os.path.isfile(FileName):  # ファイルの有無確認
            print("\tDL : " + DL_link["href"].split("/")[-1])
            urllib.request.urlretrieve(url=DL_link["href"], filename=FileName)  # debファイルDL

        # 依存関係ありのdeb
        dep_lists = pkg_soup.find_all(name="ul", class_="uldep")  # 依存pkgリスト
        if len(dep_lists) > 1:  # 依存関係リストが存在するか確認
            dep_links = dep_lists[1].find_all(name="dl")
            for dep_link in dep_links:
                dep_text = dep_link.find(name="a").get_text()
                print(dep_text)
                get_package(package, dep_text, suite, architecture)
                print("-----------------------------------------------")
        else:
            print(f"No dependency list found for {package_name}")
    else:
        print(f"No download list found for {package_name}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python debGet.py <package_name> <suite> <architecture>")
        sys.exit(1)

    package_name = sys.argv[1]
    suite = sys.argv[2]
    architecture = sys.argv[3]

    # DL用dirの初期化
    shutil.rmtree(f"./{package_name}", ignore_errors=True)  # remove -R
    os.makedirs(f"./{package_name}", exist_ok=True)  # mkdir 

    # メインパッケージを処理
    get_package(package_name, package_name, suite, architecture)

if __name__ == '__main__':
    main()
