import logging
import sys

# 必须在导入任何数据源模块之前完成日志配置。`paperscraper` 库在其自身
# `__init__.py`/`async_utils.py` 等模块的顶层代码中会调用
# `logging.basicConfig(stream=sys.stdout, ...)`，抢先占用 Python root logger。
# `logging.basicConfig()` 只有在 root logger 尚未配置 handler 时才会生效，
# 因此我们在此提前配置好指向 stderr 的 handler，可以让 paperscraper 后续的
# `basicConfig` 调用变为无操作，从而避免任何日志输出写入 stdout——
# MCP Server 通过 stdio 传输 JSON-RPC，写入 stdout 的任何非协议内容都会
# 破坏协议帧，导致客户端（如 Cherry Studio）报 "Connection closed"。
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

from .server import create_server  # noqa: E402  (须在上面的日志配置之后导入)

__version__ = "1.0.0"

__all__ = ["create_server"]
