import os
import sys
import subprocess
import argparse
import sqlite3

def ensure_base_template(target_dir, db_path):
    if os.path.exists(db_path):
        return True
        
    print(f"🔄 正在获取基础模块包...")
    base_zip = "CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
    if not os.path.exists(base_zip):
        try:
            download_url = "https://github.com/xc996/CustomPinyinDictionary/releases/download/v20260101-Tools/CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
            subprocess.run(["curl", "-L", "-o", base_zip, download_url], check=True)
            print("✅ 基础包下载完成")
        except subprocess.CalledProcessError:
            print("❌ 基础包下载失败")
            return False
        
    try:
        subprocess.run(["unzip", "-q", base_zip, "-d", target_dir], check=True)
        subprocess.run(["cp", db_path, db_path + ".bak"], check=True)
        print("✅ 数据库提取完毕")
        return True
    except subprocess.CalledProcessError:
        print("❌ 基础包解压失败")
        return False

def main():
    parser = argparse.ArgumentParser(description="自动构建字典模块")
    parser.add_argument("--keywords", type=str, required=True, help="搜索关键词，空格分隔")
    parser.add_argument("--max-len", type=int, default=5, help="保留词条的最大长度")
    args = parser.parse_args()

    # 1. 下载
    print("\n🚀 开始下载词库...")
    keywords = args.keywords.split()
    cmd_download = ["uv", "run", "scripts/sogou_downloader.py"] + keywords
    subprocess.run(cmd_download, check=True)

    # 2. 准备基础模板
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    if not ensure_base_template(target_dir, db_path):
        sys.exit(1)

    # 3. 导入
    print("\n🚀 开始导入词库...")
    scel_dir = "scel"
    if os.path.exists(scel_dir):
        scel_files = [os.path.join(scel_dir, f) for f in os.listdir(scel_dir) if f.endswith(".scel")]
        for scel_file in scel_files:
            print(f"导入: {scel_file}")
            subprocess.run(["uv", "run", "scripts/import_scel.py", scel_file, db_path], check=True)
    else:
        print("⚠️ 未找到 scel 目录，跳过导入。")

    # 4. 清理
    print(f"\n🚀 开始清理长度超过 {args.max_len} 的词条...")
    conn = sqlite3.connect(db_path, isolation_level=None)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM entry WHERE length(word) > ?", (args.max_len,))
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("DELETE FROM entry WHERE length(word) > ?", (args.max_len,))
        cursor.execute("VACUUM")
        print(f"✅ 清理完成，共删除 {count} 条数据")
    else:
        print("✅ 无需清理")
    conn.close()

    # 5. 打包
    print("\n🚀 开始重新打包模块...")
    result = subprocess.run(["shasum", "-a", "256", db_path], capture_output=True, text=True, check=True)
    sha256_hash = result.stdout.split()[0]
    with open(os.path.join(target_dir, "dict", "db.sha256"), "w") as f:
        f.write(sha256_hash + "\n")
    
    output_zip = "CustomPinyinDictionary_Gboard_Magisk_Customized.zip"
    subprocess.run(f"cd {target_dir} && zip -q -r ../{output_zip} . -x 'dict/db.bak'", shell=True, check=True)
    print(f"✅ 模块打包成功: {output_zip}")

if __name__ == "__main__":
    main()
