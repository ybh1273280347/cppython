# MyGreatTools

Python 常用工具集，开箱即用，覆盖 90%+ 开发场景。

## 痛点分析

开发时经常遇到这些问题：

| 痛点 | 示例 |
|------|------|
| 库太多记不住 | `shutil`、`zipfile`、`tarfile`、`gzip`... |
| 语法繁琐 | `p.parent.mkdir(parents=True, exist_ok=True)` |
| 功能分散 | 复制用 `shutil`，压缩用 `zipfile`，下载用 `httpx` |
| 重复造轮子 | 每个项目都写一遍断点续传、进度显示 |
| 异常处理麻烦 | 下载超时、连接失败、状态码判断... |

**MyGreatTools 解决这些问题：一个库，一套 API，搞定所有文件操作。**

---

## 一、FileTool - 文件操作工具

### 功能

| 方法 | 功能 | 特性 |
|------|------|------|
| `download` | 下载文件 | 断点续传、自动重试、进度显示 |
| `download_batch` | 批量下载 | 并发下载、自动管理任务 |
| `extract` | 解压文件 | 支持 zip/tar.gz/tgz/gz |
| `compress` | 压缩文件 | 支持 zip/tar.gz |
| `find` | 查找文件 | 按扩展名过滤、递归搜索 |
| `read` | 读取文件 | 文本/二进制、默认值 |
| `write` | 写入文件 | 自动创建目录 |
| `size` | 获取大小 | 文件/目录、可读格式 |
| `copy` | 复制 | 文件/目录、保留元数据 |
| `move` | 移动 | 文件/目录 |
| `delete` | 删除 | 单个/批量、文件/目录 |

### 安装依赖

```bash
pip install httpx
```

### 使用示例

```python
from MyGreatTools import FileTool

# 下载文件（支持断点续传）
await FileTool.download('https://example.com/file.zip', 'downloads/')

# 批量并发下载
urls = ['https://example.com/a.zip', 'https://example.com/b.zip']
results = await FileTool.download_batch(urls, 'downloads/')

# 解压
FileTool.extract('downloads/file.zip')

# 压缩
FileTool.compress('src/', 'release.zip')
FileTool.compress(['a.txt', 'b.txt'], 'files.zip')

# 查找文件
for f in FileTool.find('src', extensions=['.py'], recursive=True):
    print(f)

# 读写文件
content = FileTool.read('config.json', default='{}')
FileTool.write('output.txt', 'hello world')

# 获取大小
print(FileTool.size('downloads/'))  # 125.3 MB
print(FileTool.size('file.txt', human_readable=False))  # 1024

# 复制/移动/删除
FileTool.copy('a.txt', 'backup/a.txt')
FileTool.copy('src/', 'backup/src/')
FileTool.move('old.txt', 'new.txt')
FileTool.delete('temp.txt')
FileTool.delete(['a.txt', 'b.txt', 'temp/'])
```

### API 文档

#### download(url, root_dir, file_name=None, timeout=30.0, retries=3, chunk_size=8192)

断点续传下载。

```python
await FileTool.download(
    url='https://example.com/file.zip',
    root_dir='downloads/',
    file_name='myfile.zip',  # 可选，默认从 URL 提取
    timeout=60.0,            # 超时时间
    retries=3,               # 重试次数
    chunk_size=8192          # 块大小
)
```

#### download_batch(urls, root_dir, file_names=None, max_concurrent=5, **kwargs)

批量并发下载多个文件。

```python
urls = ['https://example.com/a.zip', 'https://example.com/b.zip']

# 全部并发下载（默认最多 5 个同时下载）
results = await FileTool.download_batch(urls, 'downloads/')

# 指定文件名
results = await FileTool.download_batch(
    urls, 
    'downloads/',
    file_names=['a.zip', 'b.zip']
)

# 限制最大并发数
results = await FileTool.download_batch(urls, 'downloads/', max_concurrent=3)

# 返回值: {url: Path 或 None}
# {'https://example.com/a.zip': Path('downloads/a.zip'), ...}
```

#### extract(file_path, extract_to_dir=None)

解压文件。

```python
FileTool.extract('file.zip')                    # 解压到 file/ 目录
FileTool.extract('file.tar.gz', 'output/')      # 解压到指定目录
```

#### compress(obj, output_file, fmt='zip')

压缩文件/目录。

```python
FileTool.compress('src/', 'release.zip')
FileTool.compress('src/', 'release.tar.gz', fmt='tar.gz')
FileTool.compress(['a.txt', 'b.txt'], 'files.zip')
```

#### find(directory, extensions=None, recursive=False)

查找文件。

```python
# 查找所有文件
for f in FileTool.find('src'):
    print(f)

# 按扩展名过滤
for f in FileTool.find('src', extensions=['.py', '.txt']):
    print(f)

# 递归搜索
for f in FileTool.find('src', extensions=['.py'], recursive=True):
    print(f)
```

#### read(path, default='', mode='text')

读取文件。

```python
content = FileTool.read('config.json')
content = FileTool.read('config.json', default='{}')  # 文件不存在返回默认值
data = FileTool.read('binary.bin', mode='bytes')
```

#### write(path, content, encoding='utf-8', mode='text')

写入文件。

```python
FileTool.write('output.txt', 'hello world')
FileTool.write('binary.bin', b'\x00\x01', mode='bytes')
```

#### size(path, human_readable=True)

获取大小。

```python
print(FileTool.size('file.txt'))       # 1.5 KB
print(FileTool.size('downloads/'))     # 125.3 MB
print(FileTool.size('file.txt', human_readable=False))  # 1536
```

#### copy(src, dst)

复制文件/目录。

```python
FileTool.copy('a.txt', 'b.txt')
FileTool.copy('a.txt', 'backup/a.txt')
FileTool.copy('src/', 'backup/src/')
```

#### move(src, dst)

移动文件/目录。

```python
FileTool.move('old.txt', 'new.txt')
FileTool.move('src/', 'dist/src/')
```

#### delete(obj)

删除文件/目录。

```python
FileTool.delete('temp.txt')
FileTool.delete('temp/')
FileTool.delete(['a.txt', 'b.txt', 'temp/'])
```

---

> FileTool 是 MyGreatTools 的第一个工具类，后续会继续添加更多实用工具。
