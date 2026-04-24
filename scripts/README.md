# Gboard 词库生成与打包工具

本项目包含用于从搜狗官网下载细胞词库并将其转换、导入为 Gboard `PersonalDictionary.db` 格式的脚本。

## 目录结构
- `scripts/sogou_downloader.py`: 自动从搜狗官网搜索并下载 `.scel` 细胞词库
- `scripts/import_scel.py`: 解析 `.scel` 格式文件，并将其中的词条导入到 SQLite 数据库中

## 依赖安装
本项目使用 `uv` 管理依赖，请确保已安装 `uv`，然后在项目根目录执行：
```bash
uv venv
source .venv/bin/activate
uv pip install requests
```

## 使用方法

### 1. 批量下载词库
运行下载脚本，并传入你想下载的词库领域关键词（支持多个）：
```bash
uv run scripts/sogou_downloader.py "网络流行" "成语" "计算机" "医学"
```
下载的词库文件会自动保存在项目根目录下的 `scel/` 文件夹中。

### 2. 导入词库到 Gboard 数据库
确保你已经有一个基础的 Gboard `PersonalDictionary.db` 文件（例如从作者发布的 Magisk 模块中解压出来的 `dict/db`），然后运行：
```bash
# 单个导入
uv run scripts/import_scel.py scel/某个词库.scel path/to/dict/db

# 批量导入所有下载的词库
for f in scel/*.scel; do uv run scripts/import_scel.py "$f" path/to/dict/db; done
```

### 3. 重新打包模块
导入完成后，请记得更新数据库的 SHA256 校验和，并重新打包：
```bash
# 假设当前在模块解压目录下
shasum -a 256 dict/db | awk '{print $1}' > dict/db.sha256
zip -r ../CustomPinyinDictionary_Gboard_MyVersion.zip . -x "dict/db.bak"
```
