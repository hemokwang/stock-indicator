import pandas as pd

class Stock:
    def __init__(self, code: str, name: str, data: pd.DataFrame = None):
        self.code = code
        self.name = name
        self.data = data if data is not None else pd.DataFrame()

class Index:
    def __init__(self, code: str, name: str, data: pd.DataFrame = None):
        self.code = code
        self.name = name
        self.data = data if data is not None else pd.DataFrame()

class ETF:
    def __init__(self, code: str, name: str, data: pd.DataFrame = None):
        self.code = code
        self.name = name
        self.data = data if data is not None else pd.DataFrame()
