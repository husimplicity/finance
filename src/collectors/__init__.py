"""消息收集器模块"""
from .base_collector import BaseCollector
from .csrc_collector import CSRCCollector
from .exchange_collector import ExchangeCollector
from .playwright_exchange_collector import PlaywrightExchangeCollector
from .eastmoney_collector import EastMoneyCollector
from .tonghuashun_collector import TongHuaShunCollector
from .xueqiu_collector import XueqiuCollector
from .bse_collector import BSECollector

__all__ = [
    'BaseCollector',
    'CSRCCollector',
    'ExchangeCollector',
    'PlaywrightExchangeCollector',
    'EastMoneyCollector',
    'TongHuaShunCollector',
    'XueqiuCollector',
    'BSECollector',
]
