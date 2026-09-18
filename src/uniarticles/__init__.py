import logging
import sys

# 必须在导入任何数据源模块之前完成日志配置——这是一层通用的 stdout 保护，
# 而非针对某个具体依赖：某些第三方库会在其模块顶层执行
# `logging.basicConfig(stream=sys.stdout, ...)`，抢先占用 Python root logger
# （v3.1.0 之前移除的 `paperscraper` 曾是一例；此类"库在 import 时抢占 root
# logger"的行为并不罕见，未来任何新增依赖都可能重蹈覆辙）。
# `logging.basicConfig()` 只有在 root logger 尚未配置 handler 时才会生效，
# 因此我们在此提前配置好指向 stderr 的 handler，使后续任何第三方的
# `basicConfig(stream=sys.stdout,...)` 调用变为无操作，从而避免日志写入 stdout——
# MCP Server 通过 stdio 传输 JSON-RPC，写入 stdout 的任何非协议内容都会
# 破坏协议帧，导致客户端（如 Cherry Studio）报 "Connection closed"。
# 保留这层防御的边际成本极低（数行代码），远低于"未来某依赖再次污染 stdout
# 又要重新排查一次"的风险，故 v3.1.0 移除 paperscraper 后仍作为通用防线保留。
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

from .server import create_server  # noqa: E402  (须在上面的日志配置之后导入)

__version__ = "3.5.0"

__all__ = ["create_server"]
