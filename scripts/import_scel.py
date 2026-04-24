import struct
import sqlite3
import sys
import os

def byte_2_str(data):
    """
    将二进制字节块转换为字符串 (UTF-16LE)
    """
    result = ""
    for i in range(0, len(data), 2):
        char_bytes = data[i:i+2]
        char = struct.unpack('<H', char_bytes)[0]
        result += chr(char)
    return result

def get_pinyin_table(data):
    """
    解析拼音表，起始位置通常在 0x1540
    """
    if data[0x1540:0x1544] != b'\x9D\x01\x00\x00':
        return None
    
    pinyin_dict = {}
    pos = 0x1544
    while pos < len(data):
        index = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        length = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        
        py = byte_2_str(data[pos:pos+length])
        pinyin_dict[index] = py
        pos += length
        
        if data[pos:pos+4] == b'\x28\x26\x00\x00' or pos >= 0x2628:
            break
            
    return pinyin_dict

def get_word_table(data, pinyin_dict):
    """
    解析词块表，起始位置通常在 0x2628
    """
    pos = 0x2628
    while pos < len(data):
        count = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        py_index_len = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        
        py_indices = []
        for i in range(0, py_index_len, 2):
            py_indices.append(struct.unpack('<H', data[pos:pos+2])[0])
            pos += 2
        
        # 搜狗词库的拼音是连在一起的，对于 Gboard，我们需要用单引号分隔
        full_pinyin = "'".join([pinyin_dict[i] for i in py_indices])
        
        for i in range(count):
            word_len = struct.unpack('<H', data[pos:pos+2])[0]
            pos += 2
            word = byte_2_str(data[pos:pos+word_len])
            pos += word_len
            pos += 12 # 跳过扩展信息
            
            yield word, full_pinyin

def import_scel_to_gboard_db(scel_path, db_path):
    """
    读取 scel 文件并导入到 Gboard SQLite 数据库
    """
    if not os.path.exists(scel_path):
        print(f"错误: 找不到细胞词库文件 {scel_path}")
        return

    if not os.path.exists(db_path):
        print(f"错误: 找不到数据库文件 {db_path}")
        return

    print(f"正在读取搜狗细胞词库: {scel_path}")
    with open(scel_path, 'rb') as f:
        data = f.read()
    
    pinyin_dict = get_pinyin_table(data)
    if not pinyin_dict:
        print(f"错误: {scel_path} 格式不正确或不受支持。")
        return

    print(f"正在连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    success_count = 0
    skip_count = 0
    
    # 获取当前数据库中已有的词条，避免重复插入
    cursor.execute("SELECT word, shortcut FROM entry")
    existing_entries = set((row[0], row[1]) for row in cursor.fetchall())

    for word, py in get_word_table(data, pinyin_dict):
        # 过滤掉过长的词
        if len(word) > 5:
            continue
            
        if (word, py) in existing_entries:
            skip_count += 1
            continue
            
        try:
            # Gboard Personal Dictionary 格式：word(词语), shortcut(拼音), locale(zh-CN)
            cursor.execute(
                "INSERT INTO entry (word, shortcut, locale) VALUES (?, ?, ?)",
                (word, py, "zh-CN")
            )
            success_count += 1
            # 将新插入的词条加入集合，防止同一个 scel 文件中有重复词
            existing_entries.add((word, py))
        except Exception as e:
            print(f"插入 [{word}] 时出错: {e}")

    conn.commit()
    conn.close()
    
    print(f"导入完成！成功新增词条: {success_count} 条，跳过重复/超长词条: {skip_count} 条。")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: uv run import_scel.py <输入文件.scel> <Gboard数据库路径>")
        sys.exit(1)
        
    scel_file = sys.argv[1]
    db_file = sys.argv[2]
    
    import_scel_to_gboard_db(scel_file, db_file)
