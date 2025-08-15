from copy import copy
from datetime import date
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
from pydantic import BaseModel


class ResultMN(BaseModel):
    """Kết quả xổ số miền Nam"""
    date: date
    province: str
    special: int
    prize1: int
    prize2: int
    prize3_1: int
    prize3_2: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize4_5: int
    prize4_6: int
    prize4_7: int
    prize5: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize7: int
    prize8: int


class ResultMNList(BaseModel):
    """Danh sách kết quả xổ số miền Nam"""
    root: List[ResultMN]


class ResultMN(BaseModel):
    date: date
    province: str

    prize8: int
    prize7: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize5: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize4_5: int
    prize4_6: int
    prize4_7: int
    prize3_1: int
    prize3_2: int
    prize2: int
    prize1: int
    special: int


class ResultMNList(BaseModel):
    root: list[ResultMN] = []


class LotteryMN:
    def __init__(self) -> None:
        self._http = CloudScraper()
        self._data: dict[date, list[ResultMN]] = {}
        self._raw_data: pd.DataFrame = pd.DataFrame()
        self._2_digits_data: pd.DataFrame = pd.DataFrame()
        self._sparse_data: pd.DataFrame = pd.DataFrame()
        self._begin_date = date.today()
        self._last_date = date.today()
        self._init_data_files()

    def _init_data_files(self) -> None:
        """Initialize required data files if they don't exist"""
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        files = [
            ('xsmn.json', '{"root": []}'),
            ('xsmn.csv', ''),
            ('xsmn-2-digits.csv', ''),
            ('xsmn-sparse.csv', '')
        ]
        
        for filename, content in files:
            file_path = data_dir / filename
            if not file_path.exists():
                print(f"Creating {filename}")
                file_path.write_text(content, encoding='utf-8')

    def load(self) -> None:
        with open('data/xsmn.json', 'r', encoding='utf-8') as f:
            data = ResultMNList.model_validate_json(f.read())
        for d in data.root:
            if d.date not in self._data:
                self._data[d.date] = []
            self._data[d.date].append(d)
        self.generate_dataframes()

    def dump(self) -> None:
        # First dump to JSON
        root = [item for sublist in self._data.values() for item in sublist]
        with open('data/xsmn.json', 'w', encoding='utf-8') as f:
            json_data = {'root': [item.model_dump() for item in root]}
            import json
            json.dump(json_data, f, indent=2, default=str)
        print(f"Saved {len(root)} results to xsmn.json")

        def _dump(df: pd.DataFrame, file_name: str) -> None:
            if not df.empty:
                df.to_csv(f'data/{file_name}.csv', index=False)
                df.to_json(f'data/{file_name}.json', orient='records', date_format='iso', indent=2)
                df.to_parquet(f'data/{file_name}.parquet', index=False)
                print(f"Saved {len(df)} records to {file_name} files")

        _dump(self._raw_data, 'xsmn')
        _dump(self._2_digits_data, 'xsmn-2-digits')
        _dump(self._sparse_data, 'xsmn-sparse')

    def fetch(self, selected_date: date) -> None:
        url = f'https://xoso.com.vn/xsmn-{selected_date:%d-%m-%Y}.html'
        resp = self._http.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch URL {url}, status code: {resp.status_code}")
            return

        soup = BeautifulSoup(resp.text, 'lxml')
        
        # Tìm bảng kết quả chính
        table = soup.find('table', {'class': 'table-result'})
        if not table:
            print(f"No result table found for date {selected_date}")
            return

        # Get provinces from header
        header = table.find('tr')
        if not header:
            print("No header row found")
            return
        
        # Skip first th which contains 'G'
        provinces = [th.text.strip() for th in header.find_all('th')[1:]]
        if not provinces:
            print("No provinces found")
            return
        
        print(f"Found provinces: {', '.join(provinces)}")

        # Initialize results dictionary
        province_results = {province: {} for province in provinces}
        
        # Process each row
        rows = table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) < 2:
                continue
            
            prize = cells[0].text.strip()
            print(f"\nProcessing prize {prize}")
            
            # Get results for each province
            for province, cell in zip(provinces, cells[1:]):
                numbers = cell.text.strip().split()
                try:
                    province_results[province][prize] = [int(n) for n in numbers] if numbers else [0]
                    print(f"  {province}: {numbers}")
                except ValueError as e:
                    print(f"Error converting numbers for {province}, prize {prize}: {e}")
                    province_results[province][prize] = [0]

        # Create ResultMN objects
        results = []
        for province in provinces:
            try:
                prizes = province_results[province]
                result = ResultMN(
                    date=selected_date,
                    province=province,
                    special=prizes.get('ĐB', [0])[0],
                    prize1=prizes.get('1', [0])[0],
                    prize2=prizes.get('2', [0])[0],
                    prize3_1=prizes.get('3', [0, 0])[0],
                    prize3_2=prizes.get('3', [0, 0])[1] if len(prizes.get('3', [])) > 1 else 0,
                    prize4_1=prizes.get('4', [0]*7)[0],
                    prize4_2=prizes.get('4', [0]*7)[1] if len(prizes.get('4', [])) > 1 else 0,
                    prize4_3=prizes.get('4', [0]*7)[2] if len(prizes.get('4', [])) > 2 else 0,
                    prize4_4=prizes.get('4', [0]*7)[3] if len(prizes.get('4', [])) > 3 else 0,
                    prize4_5=prizes.get('4', [0]*7)[4] if len(prizes.get('4', [])) > 4 else 0,
                    prize4_6=prizes.get('4', [0]*7)[5] if len(prizes.get('4', [])) > 5 else 0,
                    prize4_7=prizes.get('4', [0]*7)[6] if len(prizes.get('4', [])) > 6 else 0,
                    prize5=prizes.get('5', [0])[0],
                    prize6_1=prizes.get('6', [0, 0, 0])[0],
                    prize6_2=prizes.get('6', [0, 0, 0])[1] if len(prizes.get('6', [])) > 1 else 0,
                    prize6_3=prizes.get('6', [0, 0, 0])[2] if len(prizes.get('6', [])) > 2 else 0,
                    prize7=prizes.get('7', [0])[0],
                    prize8=prizes.get('8', [0])[0]
                )
                results.append(result)
                print(f"Successfully processed data for {province}")
            except Exception as e:
                print(f"Error creating result for {province}: {e}")

        if results:
            self._data[selected_date] = results
            print(f"Successfully fetched {len(results)} results for date {selected_date}")
            self.generate_dataframes()
        else:
            print(f"No valid results found for date {selected_date}")

    def generate_dataframes(self) -> None:
        if not self._data:
            print("No data to generate dataframes")
            return

        all_results = []
        for results_in_date in self._data.values():
            all_results.extend([d.model_dump() for d in results_in_date])

        if not all_results:
            print("No results to process")
            return

        self._raw_data = pd.DataFrame(all_results)
        self._raw_data['date'] = pd.to_datetime(self._raw_data['date'])
        numeric_cols = self._raw_data.columns.difference(['date', 'province'])
        self._raw_data[numeric_cols] = self._raw_data[numeric_cols].astype('int64')

        self._2_digits_data = copy(self._raw_data)
        self._2_digits_data[numeric_cols] = self._2_digits_data[numeric_cols].apply(lambda x: x % 100)

        self._sparse_data = pd.concat(
            [
                self._2_digits_data[['date', 'province']],
                pd.DataFrame(np.zeros((len(self._2_digits_data), 100), dtype=int)),
            ],
            axis=1,
        )
        
        for i in range(len(self._2_digits_data)):
            counts = self._2_digits_data.iloc[i, 2:].value_counts()
            for k, v in counts.items():
                if 0 <= k < 100:  # Ensure the number is within valid range
                    self._sparse_data.iloc[i, k + 2] = int(v)

        if not self._raw_data.empty:
            begin_date = self._raw_data['date'].min()
            self._begin_date = begin_date.to_pydatetime().date()
            last_date = self._raw_data['date'].max()
            self._last_date = last_date.to_pydatetime().date()
            print(f"Generated dataframes with data from {self._begin_date} to {self._last_date}")

    def get_raw_data(self) -> pd.DataFrame:
        return self._raw_data

    def get_2_digits_data(self) -> pd.DataFrame:
        return self._2_digits_data

    def get_sparse_data(self) -> pd.DataFrame:
        return self._sparse_data

    def get_last_date(self) -> date:
        return self._last_date
