from copy import copy
from datetime import date
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
from pydantic import BaseModel


class ResultMT(BaseModel):
    """Kết quả xổ số miền Trung"""
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


class ResultMTList(BaseModel):
    """Danh sách kết quả xổ số miền Trung"""
    root: List[ResultMT]


class ResultMT(BaseModel):
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


class ResultMTList(BaseModel):
    root: list[ResultMT] = []


class LotteryMT:
    def __init__(self) -> None:
        self._http = CloudScraper()
        self._data: dict[date, list[ResultMT]] = {}
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
            ('xsmt.json', '{"root": []}'),
            ('xsmt.csv', ''),
            ('xsmt-2-digits.csv', ''),
            ('xsmt-sparse.csv', '')
        ]
        
        for filename, content in files:
            file_path = data_dir / filename
            if not file_path.exists():
                print(f"Creating {filename}")
                file_path.write_text(content, encoding='utf-8')

    def get_last_date(self) -> date:
        if len(self._data) == 0:
            return self._last_date
        return max(self._data.keys())

    def load(self) -> None:
        with open('data/xsmt.json', 'r', encoding='utf-8') as f:
            data = ResultMTList.model_validate_json(f.read())
        for d in data.root:
            if d.date not in self._data:
                self._data[d.date] = []
            self._data[d.date].append(d)
        self.generate_dataframes()

    def dump(self) -> None:
        # First dump to JSON
        root = [item for sublist in self._data.values() for item in sublist]
        with open('data/xsmt.json', 'w', encoding='utf-8') as f:
            json_data = {'root': [item.model_dump() for item in root]}
            import json
            json.dump(json_data, f, indent=2, default=str)
        print(f"Saved {len(root)} results to xsmt.json")

        def _dump(df: pd.DataFrame, file_name: str) -> None:
            if not df.empty:
                df.to_csv(f'data/{file_name}.csv', index=False)
                df.to_json(f'data/{file_name}.json', orient='records', date_format='iso', indent=2)
                df.to_parquet(f'data/{file_name}.parquet', index=False)
                print(f"Saved {len(df)} records to {file_name} files")

        _dump(self._raw_data, 'xsmt')
        _dump(self._2_digits_data, 'xsmt-2-digits')
        _dump(self._sparse_data, 'xsmt-sparse')

    def fetch(self, selected_date: date) -> None:
        url = f'https://xoso.com.vn/xsmt-{selected_date:%d-%m-%Y}.html'
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

        # Create ResultMT objects
        results = []
        for province in provinces:
            try:
                prizes = province_results[province]
                result = ResultMT(
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

        # Prepare raw data
        all_results = []
        for results in self._data.values():
            for result in results:
                row = copy(result.__dict__)
                all_results.append(row)
        
        self._raw_data = pd.DataFrame(all_results)

        # Last 2 digits data
        if len(self._raw_data) > 0:
            digits_data = []
            for _, row in self._raw_data.iterrows():
                date_val = row['date']
                province = row['province']
                # Convert each prize to last 2 digits
                digits = {
                    'date': date_val,
                    'province': province,
                    'special': row['special'] % 100,
                    'prize1': row['prize1'] % 100,
                    'prize2': row['prize2'] % 100
                }
                
                # Add prize3 digits
                for i in [1, 2]:
                    digits[f'prize3_{i}'] = row[f'prize3_{i}'] % 100

                # Add prize4 digits
                for i in range(1, 8):
                    digits[f'prize4_{i}'] = row[f'prize4_{i}'] % 100

                digits['prize5'] = row['prize5'] % 100
                
                # Add prize6 digits
                for i in [1, 2, 3]:
                    digits[f'prize6_{i}'] = row[f'prize6_{i}'] % 100

                digits['prize7'] = row['prize7'] % 100
                digits['prize8'] = row['prize8']
                
                digits_data.append(digits)

            self._2_digits_data = pd.DataFrame(digits_data)

        # Generate sparse data
        if len(self._raw_data) > 0:
            sparse_data = []
            for _, row in self._raw_data.iterrows():
                date_val = row['date']
                province = row['province']
                # Special prize
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'special',
                    'number': row['special'],
                    'prize_index': 0
                })
                
                # Prize 1
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'prize1',
                    'number': row['prize1'],
                    'prize_index': 0
                })

                # Prize 2
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'prize2',
                    'number': row['prize2'],
                    'prize_index': 0
                })

                # Prize 3
                for i in [1, 2]:
                    if row[f'prize3_{i}'] != 0:
                        sparse_data.append({
                            'date': date_val,
                            'province': province,
                            'prize_type': 'prize3',
                            'number': row[f'prize3_{i}'],
                            'prize_index': i
                        })

                # Prize 4
                for i in range(1, 8):
                    if row[f'prize4_{i}'] != 0:
                        sparse_data.append({
                            'date': date_val,
                            'province': province,
                            'prize_type': 'prize4',
                            'number': row[f'prize4_{i}'],
                            'prize_index': i
                        })

                # Prize 5
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'prize5',
                    'number': row['prize5'],
                    'prize_index': 0
                })

                # Prize 6
                for i in [1, 2, 3]:
                    if row[f'prize6_{i}'] != 0:
                        sparse_data.append({
                            'date': date_val,
                            'province': province,
                            'prize_type': 'prize6',
                            'number': row[f'prize6_{i}'],
                            'prize_index': i
                        })

                # Prize 7
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'prize7',
                    'number': row['prize7'],
                    'prize_index': 0
                })

                # Prize 8
                sparse_data.append({
                    'date': date_val,
                    'province': province,
                    'prize_type': 'prize8',
                    'number': row['prize8'],
                    'prize_index': 0
                })

            self._sparse_data = pd.DataFrame(sparse_data)
