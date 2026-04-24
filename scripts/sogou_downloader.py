import os
import re
import urllib.parse
import requests

def search_and_download_sogou_dicts(keyword, max_pages=1, save_dir="scel"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"正在搜索搜狗词库关键词: '{keyword}'...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    url_word = urllib.parse.quote(keyword.encode('GBK'))
    downloaded_files = []

    for page in range(1, max_pages + 1):
        url = f'https://pinyin.sogou.com/dict/search/search_list/{url_word}/normal/{page}'
        try:
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            html = response.text

            # 匹配类似 //pinyin.sogou.com/d/dict/download_cell.php?id=xxxx&name=xxxx 的下载链接
            matches = re.findall(r'download_cell\.php\?[^"]+', html)
            if not matches:
                print(f"第 {page} 页没有找到更多结果。")
                break

            for link in set(matches):
                download_url = 'https://pinyin.sogou.com/d/dict/' + link
                
                # 从链接中解析出 name
                # ?id=43900&name=%C9%CF%BA%A3%BB%B0%B4%CA%BB%E3
                parsed = urllib.parse.urlparse(download_url)
                qs = urllib.parse.parse_qs(parsed.query)
                name = qs.get('name', ['unknown'])[0]
                
                # 搜狗 URL 中的中文通常是 GBK 编码
                try:
                    name_decoded = name.encode('latin1').decode('gbk')
                except:
                    name_decoded = urllib.parse.unquote(name)

                # 去除非法字符
                safe_name = re.sub(r'[\\/*?:"<>|]', "", name_decoded)
                file_path = os.path.join(save_dir, f"{safe_name}.scel")

                if os.path.exists(file_path):
                    print(f"已存在跳过: {safe_name}.scel")
                    continue

                print(f"正在下载: {safe_name}.scel ...")
                dict_resp = requests.get(download_url, headers=headers)
                if dict_resp.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(dict_resp.content)
                    downloaded_files.append(file_path)
                else:
                    print(f"下载失败: {download_url}")

        except Exception as e:
            print(f"搜索出错: {e}")
            break

    print(f"'{keyword}' 搜索及下载完成，共下载 {len(downloaded_files)} 个词库。")
    return downloaded_files

if __name__ == "__main__":
    import sys
    keywords = sys.argv[1:] if len(sys.argv) > 1 else ["网络", "上海"]
    for kw in keywords:
        search_and_download_sogou_dicts(kw, max_pages=1, save_dir="scel")
