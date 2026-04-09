"""
文件操作工具集

提供下载、解压、压缩、查找、读写等常用文件操作。
"""

import asyncio
import gzip
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import httpx # pyright: ignore[reportMissingImports]
from httpx import HTTPTransport # pyright: ignore[reportMissingImports]


class FileTool:
    """
    文件操作工具类（全部为静态方法）

    功能：
        - download: 断点续传下载
        - download_batch: 批量并发下载
        - extract: 解压压缩文件
        - compress: 压缩文件/目录
        - find: 查找文件
        - read/write: 文件读写
        - size: 获取文件/目录大小
        - copy: 复制文件/目录
        - move: 移动文件/目录
        - delete: 删除文件/目录

    Example:
        await FileTool.download('https://example.com/file.zip', 'downloads/')
        await FileTool.download_batch(['url1', 'url2'], 'downloads/')
        FileTool.extract('downloads/file.zip', 'output/')
        FileTool.copy('src.txt', 'dst.txt')
        FileTool.move('old.txt', 'new.txt')
        FileTool.delete('temp/')
    """

    @staticmethod
    async def download(url, root_dir, file_name=None, timeout=30.0, retries=3, chunk_size=8192):
        """
        支持断点续传的异步下载

        Args:
            url: 下载链接
            root_dir: 保存目录
            file_name: 文件名（可选，默认从 URL 提取）
            timeout: 请求超时时间（秒）
            retries: 请求重试次数
            chunk_size: 下载块大小

        Returns:
            下载成功返回文件路径，失败返回 None
        """
        root_dir = Path(root_dir)
        root_dir.mkdir(parents=True, exist_ok=True)
        
        # 从 URL 提取文件名
        file_name = Path(file_name) if file_name else Path(urlparse(url).path).name
        save_path = root_dir / file_name

        # 断点续传：获取已下载大小
        existing_size = save_path.stat().st_size if save_path.exists() else 0
        headers = {'Range': f'bytes={existing_size}-'} if existing_size else {}

        try:
            transport = HTTPTransport(retries=retries)
            async with httpx.AsyncClient(transport=transport) as client:
                async with client.stream(
                    "GET", url,
                    headers=headers,
                    timeout=timeout,
                    follow_redirects=True  # 自动跟随重定向
                ) as response:
                    # 416 表示 Range 无效，文件已完整下载
                    if response.status_code == 416:
                        print(f'文件已完整下载: {save_path}')
                        return save_path

                    # 206 剩余部分内容（断点续传），200 完整内容
                    if response.status_code == 206:
                        remaining = int(response.headers.get('content-length', 0))
                        total = remaining + existing_size
                    elif response.status_code == 200:
                        total = int(response.headers.get('content-length', 0))
                        existing_size = 0  # 从头开始下载
                    else:
                        print(f'下载失败: {response.status_code}')
                        return None

                    # ab 追加模式用于断点续传，wb 写入模式用于新下载
                    mode = 'ab' if existing_size else 'wb'
                    with open(save_path, mode) as f:
                        print(f"下载中: {file_name}...")
                        downloaded = existing_size
                        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                percent = downloaded / total * 100
                                print(f'\r进度: {downloaded}/{total} ({percent:.1f}%)', end='', flush=True)

                    print(f"\n下载完成: {save_path}")
                    return save_path

        except httpx.TimeoutException:
            print(f'请求超时: {url}')
        except httpx.ConnectError:
            print(f'连接失败: {url}')
        except httpx.HTTPStatusError as e:
            print(f'HTTP 错误: {e.response.status_code}')
        except httpx.RequestError as e:
            print(f'请求异常: {e}')
        
        return None
    
    @staticmethod
    async def download_batch(urls, root_dir, file_names=None, max_concurrent=5, **kwargs):
        """
        批量并发下载多个文件

        Args:
            urls: 下载链接列表
            root_dir: 保存目录
            file_names: 文件名列表（可选，默认从 URL 提取）
            max_concurrent: 最大并发数（默认 5）
            **kwargs: 传递给 download 的参数（timeout, retries 等）

        Returns:
            dict: {url: Path 或 None}，下载成功返回路径，失败返回 None
        """
        if file_names is None:
            file_names = [None] * len(urls)
        assert len(file_names) == len(urls), "urls 和 file_names 长度必须一致"

        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_one(url, file_name):
            async with semaphore:
                return await FileTool.download(url, root_dir, file_name, **kwargs)

        tasks = [
            download_one(url, file_name) 
            for url, file_name in zip(urls, file_names)
        ]
        results = await asyncio.gather(*tasks)
        
        return {url: result for url, result in zip(urls, results)}

    @staticmethod
    def extract(file_path, extract_to_dir=None):
        """
        解压压缩文件

        Args:
            file_path: 压缩文件路径
            extract_to_dir: 解压目录（默认为同名目录）

        Returns:
            解压后的文件/目录路径
        """
        file_path = Path(file_path)
        suffix = file_path.suffix
        suffixes = file_path.suffixes

        print(f'解压中: {file_path.name}...')

        # 单独的 .gz 文件（非 .tar.gz）
        if suffix == '.gz' and len(suffixes) == 1:
            output_path = file_path.parent / file_path.stem
            with gzip.open(file_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f'解压完成: {output_path}')
            return output_path

        # 创建解压目录（默认为压缩文件同名目录）
        extract_to_dir = Path(extract_to_dir) if extract_to_dir else file_path.parent / file_path.stem
        extract_to_dir.mkdir(parents=True, exist_ok=True)

        # 根据后缀选择解压方式
        if suffix == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.extractall(extract_to_dir)

        elif suffix == '.tgz' or (len(suffixes) >= 2 and ''.join(suffixes) == '.tar.gz'):
            with tarfile.open(file_path, 'r:gz') as tar_file:
                tar_file.extractall(extract_to_dir)
        else:
            print(f'不支持的格式: {file_path}')
            return None

        print(f'解压完成: {extract_to_dir}')
        return extract_to_dir

    @staticmethod
    async def download_and_extract(url, output_dir, file_name=None, remove=True):
        """
        下载并解压

        Args:
            url: 下载链接
            output_dir: 输出目录
            file_name: 文件名（可选）
            remove: 是否删除压缩包

        Returns:
            解压后的目录路径
        """
        if remove:
            # 下载到临时目录，解压后自动清理
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = await FileTool.download(url, tmp_dir, file_name)
                if tmp_path:
                    return FileTool.extract(tmp_path, output_dir)
        else:
            # 保留压缩包
            file_path = await FileTool.download(url, output_dir, file_name)
            if file_path:
                return FileTool.extract(file_path, output_dir)

        return None

    @staticmethod
    def find(dir, extensions=None, recursive=False):
        """
        查找目录下的文件

        Args:
            dir: 搜索目录
            extensions: 文件扩展名列表，如 ['.py', '.txt']
            recursive: 是否递归搜索

        Yields:
            文件路径
        """
        dir = Path(dir)
        if not dir.exists():
            return iter(())

        # 选择递归或非递归的 glob 方法
        glob_func = dir.rglob if recursive else dir.glob

        if extensions:
            exts = set(extensions)
            return (f for f in glob_func('*') if f.is_file() and f.suffix in exts)

        return (f for f in glob_func('*') if f.is_file())

    @staticmethod
    def write(path, content, encoding='utf-8', mode='text'):
        """
        写入文件

        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码
            mode: 'text' 或 'bytes'

        Returns:
            写入的字节数
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        if mode == 'bytes':
            return p.write_bytes(content)
        return p.write_text(content, encoding=encoding)

    @staticmethod
    def read(path, default='', mode='text'):
        """
        读取文件

        Args:
            path: 文件路径
            default: 文件不存在时的默认值
            mode: 'text' 或 'bytes'

        Returns:
            文件内容
        """
        p = Path(path)
        if not p.exists():
            return default
        
        if mode == 'bytes':
            return p.read_bytes()
        return p.read_text(encoding='utf-8')

    @staticmethod
    def size(path, human_readable=True):
        """
        获取文件/目录大小

        Args:
            path: 文件/目录路径
            human_readable: 是否返回可读格式

        Returns:
            大小（字节或可读字符串）
        """
        p = Path(path)
        
        # 文件直接获取大小，目录递归计算
        if p.is_file():
            size = p.stat().st_size
        else:
            size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())

        # 转换为可读格式
        if human_readable:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f'{size:.1f} {unit}'
                size /= 1024
            return f'{size:.1f} TB'
        
        return size

    @staticmethod
    def compress(obj, output_file, fmt='zip'):
        """
        压缩文件/目录

        Args:
            obj: 文件/目录路径或路径列表
            output_file: 输出文件路径
            fmt: 压缩格式

        Returns:
            压缩文件路径
        """
        if fmt not in ('zip', 'tgz', 'tar.gz'):
            raise NotImplementedError(f'不支持 {fmt} 压缩，只支持 zip, tgz, tar.gz')

        # 统一转换为列表
        obj = [Path(f) for f in obj] if isinstance(obj, (list, tuple)) else [Path(obj)]

        if fmt == 'zip':
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in obj:
                    if p.is_file():
                        # 单文件：只保存文件名
                        zf.write(p, p.name)
                    else:
                        # 目录：保留相对路径结构
                        for f in filter(Path.is_file, p.rglob('*')):
                            zf.write(f, f.relative_to(p))
        else:
            # tar.gz 格式
            with tarfile.open(output_file, 'w:gz') as tf:
                for p in obj:
                    # tarfile 自动递归处理目录
                    tf.add(p, arcname=p.name)
        
        return Path(output_file)

    @staticmethod
    def copy(src, dst):
        """
        复制文件/目录

        Args:
            src: 源文件/目录路径
            dst: 目标文件/目录路径

        Returns:
            目标文件/目录路径
        """
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst)
        return dst
    
    @staticmethod
    def move(src, dst):
        """
        移动文件/目录

        Args:
            src: 源文件/目录路径
            dst: 目标文件/目录路径

        Returns:
            目标文件/目录路径
        """
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        return dst
    
    @staticmethod
    def delete(obj):
        """
        删除文件/目录

        Args:
            obj: 文件/目录路径或路径列表

        Returns:
            None
        """
        paths = [Path(f) for f in obj] if isinstance(obj, (list, tuple)) else [Path(obj)]
        for p in paths:
            if p.is_file():
                p.unlink(missing_ok=True)
            elif p.is_dir():
                shutil.rmtree(p)
       
