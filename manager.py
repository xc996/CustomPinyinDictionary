import os
import sys
import subprocess
try:
    import readline
except ImportError:
    pass

def print_menu():
    print("="*40)
    print("   CustomPinyinDictionary 管理工具箱")
    print("="*40)
    print("1. 📥 批量下载搜狗细胞词库 (.scel)")
    print("2. 💾 导入词库到 Gboard 数据库 (合并去重)")
    print("3. 🧹 清理数据库中的超长无用词条")
    print("4. 📦 打包生成 Magisk 刷机包 (.zip)")
    print("0. 退出")
    print("="*40)

def ensure_base_template(target_dir, db_path):
    """确保基础模板和数据库存在，不存在则自动下载解压"""
    if os.path.exists(db_path):
        return True
        
    print(f"\n⚠️ 找不到目标数据库 ({db_path})！")
    print("🔄 正在自动从基础模块包中解压提取...")
    base_zip = "CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
    if not os.path.exists(base_zip):
        print(f"❌ 找不到基础包 {base_zip}，正在从 GitHub 自动下载最新基础包...")
        try:
            download_url = "https://github.com/wuhgit/CustomPinyinDictionary/releases/download/assets/CustomPinyinDictionary_Gboard_Magisk_20260101.zip"
            subprocess.run(["curl", "-L", "-o", base_zip, download_url], check=True)
            print("✅ 基础包自动下载完成！")
        except subprocess.CalledProcessError:
            print("❌ 自动下载基础包失败，请检查网络连接或手动下载至项目根目录。")
            return False
        
    try:
        subprocess.run(["unzip", "-q", base_zip, "-d", target_dir], check=True)
        subprocess.run(["cp", db_path, db_path + ".bak"], check=True)
        print("✅ 基础数据库提取完毕！")
        return True
    except subprocess.CalledProcessError:
        print("❌ 解压基础包失败！")
        return False

def run_download():
    keywords_input = input("\n请输入想要下载的词库关键词 (多个关键词请用空格分隔，如 '网络 成语 医学'): ").strip()
    if not keywords_input:
        print("关键词不能为空！")
        return
    
    # 将输入的字符串拆分成列表
    keywords = keywords_input.split()
    
    print("\n🚀 开始执行下载脚本...")
    # 构建命令：uv run scripts/sogou_downloader.py "词1" "词2"
    cmd = ["uv", "run", "scripts/sogou_downloader.py"] + keywords
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 下载流程执行完毕！\n")
    except subprocess.CalledProcessError:
        print("❌ 下载脚本执行过程中发生错误！\n")
    except FileNotFoundError:
        print("❌ 找不到 uv 命令，请确保已安装并配置环境变量。\n")

def run_import():
    # 确认需要操作的数据库路径
    # 由于刚才解压的临时文件夹被清理了，这里为了演示和稳妥起见，
    # 我们可以先检查一下当前目录是否存在目标数据库。
    # 默认情况下，我们可以先解压一个基础的模板包来获取 db
    
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return

    scel_dir = "scel"
    if not os.path.exists(scel_dir) or not os.listdir(scel_dir):
        print("\n⚠️ scel 文件夹为空，请先执行步骤 1 下载词库！\n")
        return
        
    print("\n🚀 开始执行导入脚本...")
    scel_files = [os.path.join(scel_dir, f) for f in os.listdir(scel_dir) if f.endswith(".scel")]
    
    success_count = 0
    for scel_file in scel_files:
        cmd = ["uv", "run", "scripts/import_scel.py", scel_file, db_path]
        try:
            # 捕获输出以避免刷屏，或者直接运行展示细节
            subprocess.run(cmd, check=True)
            success_count += 1
        except subprocess.CalledProcessError:
            print(f"❌ 导入 {scel_file} 时发生错误！")
            
    print(f"✅ 导入流程执行完毕！成功处理了 {success_count} 个词库文件。\n")

def run_clean():
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return
        
    length_input = input("\n👉 请输入要清理的词条长度阈值（超过该长度的词条将被删除，默认直接回车为 5）: ").strip()
    if not length_input:
        max_len = 5
    else:
        try:
            max_len = int(length_input)
            if max_len < 1:
                raise ValueError
        except ValueError:
            print("⚠️ 无效的输入，必须为大于0的整数！\n")
            return
            
    print(f"\n🚀 开始清理数据库中长度超过 {max_len} 个字的词条...")
    
    try:
        import sqlite3
        # 使用 isolation_level=None 启用自动提交模式，这是执行 VACUUM 的必要条件
        conn = sqlite3.connect(db_path, isolation_level=None)
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM entry WHERE length(word) > ?", (max_len,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ 数据库中没有长度超过 {max_len} 的词条，无需清理。\n")
        else:
            cursor.execute("DELETE FROM entry WHERE length(word) > ?", (max_len,))
            cursor.execute("VACUUM")
            print(f"✅ 清理成功！共删除了 {count} 条超长无用词条，并对数据库进行了碎片整理（VACUUM）。\n")
            
        conn.close()
    except Exception as e:
        print(f"❌ 数据库清理失败: {e}\n")

def run_pack():
    target_dir = "CustomPinyinDictionary_Gboard_Magisk_Template"
    db_path = os.path.join(target_dir, "dict", "db")
    
    if not ensure_base_template(target_dir, db_path):
        return
        
    print("\n🚀 开始重新打包 Magisk 模块...")
    
    # 重新计算 sha256 校验和
    try:
        # 使用 shasum -a 256
        result = subprocess.run(["shasum", "-a", "256", db_path], capture_output=True, text=True, check=True)
        sha256_hash = result.stdout.split()[0]
        
        with open(os.path.join(target_dir, "dict", "db.sha256"), "w") as f:
            f.write(sha256_hash + "\n")
        print("✅ 数据库校验和更新完毕！")
    except Exception as e:
        print(f"❌ 更新校验和失败: {e}")
        return

    # 执行 zip 打包
    output_zip = "../CustomPinyinDictionary_Gboard_Magisk_Customized.zip"
    try:
        # 切换到目录内部打包，这样 zip 内部结构才是正确的
        cmd = f"cd {target_dir} && zip -q -r {output_zip} . -x 'dict/db.bak'"
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ 打包成功！产物位置: CustomPinyinDictionary_Gboard_Magisk_Customized.zip\n")
    except subprocess.CalledProcessError:
        print("❌ 打包过程发生错误！\n")

def main():
    while True:
        print_menu()
        choice = input("👉 请输入序号选择功能: ").strip()
        
        if choice == '1':
            run_download()
        elif choice == '2':
            run_import()
        elif choice == '3':
            run_clean()
        elif choice == '4':
            run_pack()
        elif choice == '0':
            print("👋 感谢使用，再见！")
            sys.exit(0)
        else:
            print("⚠️ 无效的输入，请重新选择！\n")

if __name__ == "__main__":
    # 确保脚本在项目根目录运行
    if not os.path.exists("scripts/sogou_downloader.py"):
        print("❌ 请在项目根目录下运行此脚本！")
        sys.exit(1)
        
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 已取消操作。")
        sys.exit(0)
