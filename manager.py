import os
import sys
import subprocess
try:
    import readline
except ImportError:
    pass

def print_menu():
    print("="*40)
    print("   CustomPinyinDictionary 模块管理工具")
    print("="*40)
    print("1. 📥 下载搜狗细胞词库 (.scel)")
    print("2. 💾 导入词库到 Gboard 数据库")
    print("3. 🧹 清理数据库中的超长词条")
    print("4. 📦 重新打包 Magisk 模块 (.zip)")
    print("0. 退出")
    print("="*40)

def ensure_base_template(target_dir, db_path):
    """检查基础模板和数据库状态，如缺失则自动获取"""
    if os.path.exists(db_path):
        return True
        
    print(f"\n⚠️ 未检测到目标数据库 ({db_path})")
    print("🔄 正在从基础模块包中提取...")
    base_zip = "CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
    if not os.path.exists(base_zip):
        print(f"提示: 未找到基础包 {base_zip}，正在尝试自动下载...")
        try:
            download_url = "https://github.com/wuhgit/CustomPinyinDictionary/releases/download/assets/CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
            subprocess.run(["curl", "-L", "-o", base_zip, download_url], check=True)
            print("✅ 基础包下载完成")
        except subprocess.CalledProcessError:
            print("❌ 基础包下载失败，请检查网络连接或手动下载至项目根目录")
            return False
        
    try:
        subprocess.run(["unzip", "-q", base_zip, "-d", target_dir], check=True)
        subprocess.run(["cp", db_path, db_path + ".bak"], check=True)
        print("✅ 数据库提取完毕")
        return True
    except subprocess.CalledProcessError:
        print("❌ 基础包解压失败")
        return False

def run_download():
    keywords_input = input("\n请输入需要下载的词库关键词 (多个关键词请用空格分隔): ").strip()
    if not keywords_input:
        print("关键词不能为空")
        return
    
    keywords = keywords_input.split()
    
    print("\n🚀 开始执行下载任务...")
    cmd = ["uv", "run", "scripts/sogou_downloader.py"] + keywords
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 下载任务执行完毕\n")
    except subprocess.CalledProcessError:
        print("❌ 下载脚本执行异常\n")
    except FileNotFoundError:
        print("❌ 找不到 uv 命令，请检查环境配置\n")

def run_import():
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return

    scel_dir = "scel"
    if not os.path.exists(scel_dir) or not os.listdir(scel_dir):
        print("\n⚠️ 目录为空，请先执行下载操作\n")
        return
        
    print("\n🚀 开始执行导入任务...")
    scel_files = [os.path.join(scel_dir, f) for f in os.listdir(scel_dir) if f.endswith(".scel")]
    
    success_count = 0
    for scel_file in scel_files:
        cmd = ["uv", "run", "scripts/import_scel.py", scel_file, db_path]
        try:
            subprocess.run(cmd, check=True)
            success_count += 1
        except subprocess.CalledProcessError:
            print(f"❌ 导入 {scel_file} 时发生错误")
            
    print(f"✅ 导入任务完成，成功处理 {success_count} 个文件\n")

def run_clean():
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return
        
    length_input = input("\n请输入保留词条的最大长度（默认: 5）: ").strip()
    if not length_input:
        max_len = 5
    else:
        try:
            max_len = int(length_input)
            if max_len < 1:
                raise ValueError
        except ValueError:
            print("⚠️ 输入无效，请输入正整数\n")
            return
            
    print(f"\n🚀 开始清理长度超过 {max_len} 的词条...")
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path, isolation_level=None)
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM entry WHERE length(word) > ?", (max_len,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ 数据库中无匹配词条，无需清理\n")
        else:
            cursor.execute("DELETE FROM entry WHERE length(word) > ?", (max_len,))
            cursor.execute("VACUUM")
            print(f"✅ 清理完成，共删除 {count} 条数据，并完成数据库重整\n")
            
        conn.close()
    except Exception as e:
        print(f"❌ 数据库操作异常: {e}\n")

def run_pack():
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return
        
    print("\n🚀 开始执行打包任务...")
    
    try:
        result = subprocess.run(["shasum", "-a", "256", db_path], capture_output=True, text=True, check=True)
        sha256_hash = result.stdout.split()[0]
        
        with open(os.path.join(target_dir, "dict", "db.sha256"), "w") as f:
            f.write(sha256_hash + "\n")
        print("✅ 校验和更新完成")
    except Exception as e:
        print(f"❌ 校验和更新失败: {e}")
        return

    output_zip = "../CustomPinyinDictionary_Gboard_Magisk_Customized.zip"
    try:
        cmd = f"cd {target_dir} && zip -q -r {output_zip} . -x 'dict/db.bak'"
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ 模块打包成功，产物位置: CustomPinyinDictionary_Gboard_Magisk_Customized.zip\n")
    except subprocess.CalledProcessError:
        print("❌ 打包过程发生异常\n")

def main():
    while True:
        print_menu()
        choice = input("请输入序号选择功能: ").strip()
        
        if choice == '1':
            run_download()
        elif choice == '2':
            run_import()
        elif choice == '3':
            run_clean()
        elif choice == '4':
            run_pack()
        elif choice == '0':
            print("退出程序")
            sys.exit(0)
        else:
            print("⚠️ 无效的输入，请重新选择\n")

if __name__ == "__main__":
    if not os.path.exists("scripts/sogou_downloader.py"):
        print("❌ 请在项目根目录下运行此脚本")
        sys.exit(1)
        
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
