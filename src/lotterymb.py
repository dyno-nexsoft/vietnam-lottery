from copy import copy
from datetime import date
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
from pydantic import BaseModel


class ResultMB(BaseModel):
    """Kết quả xổ số miền Bắc"""
    date: date
    special: int
    prize1: int
    prize2_1: int
    prize2_2: int
    prize3_1: int
    prize3_2: int
    prize3_3: int
    prize3_4: int
    prize3_5: int
    prize3_6: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize5_1: int
    prize5_2: int
    prize5_3: int
    prize5_4: int
    prize5_5: int
    prize5_6: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize7_1: int
    prize7_2: int
    prize7_3: int
    prize7_4: int


class ResultMBList(BaseModel):
    """Danh sách kết quả xổ số miền Bắc"""
    root: List[ResultMB]


class ResultMB(BaseModel):
    date: date
    special: int
    prize1: int
    prize2_1: int
    prize2_2: int
    prize3_1: int
    prize3_2: int
    prize3_3: int
    prize3_4: int
    prize3_5: int
    prize3_6: int
    prize4_1: int
    prize4_2: int
    prize4_3: int
    prize4_4: int
    prize5_1: int
    prize5_2: int
    prize5_3: int
    prize5_4: int
    prize5_5: int
    prize5_6: int
    prize6_1: int
    prize6_2: int
    prize6_3: int
    prize7_1: int
    prize7_2: int
    prize7_3: int
    prize7_4: int


class ResultMBList(BaseModel):
    root: List[ResultMB]


class LotteryMB:
    def __init__(self) -> None:
        self._http = CloudScraper()
        self._data: dict[date, ResultMB] = {}
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
            ('xsmb.json', '{"root": []}'),
            ('xsmb.csv', ''),
            ('xsmb-2-digits.csv', ''),
            ('xsmb-sparse.csv', '')
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
        try:
            with open('data/xsmb.json', 'r', encoding='utf-8') as f:
                data = ResultMBList.model_validate_json(f.read())
            for d in data.root:
                self._data[d.date] = d
            self.generate_dataframes()
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")

    def dump(self) -> None:
        if not self._data:
            print("No data to save")
            return

        # Convert data to list and sort by date
        data_list = list(self._data.values())
        data_list.sort(key=lambda x: x.date)
        
        # Create ResultMBList
        result_list = ResultMBList(root=data_list)
        
        # Save JSON
        with open('data/xsmb.json', 'w', encoding='utf-8') as f:
            f.write(result_list.model_dump_json(indent=2))
        
        print(f"Saved {len(data_list)} results to xsmb.json")
        
        if not self._raw_data.empty:
            self._raw_data.to_csv('data/xsmb.csv', index=False)
            self._raw_data.to_parquet('data/xsmb.parquet', index=False)
            print(f"Saved {len(self._raw_data)} records to xsmb files")
            
        if not self._2_digits_data.empty:
            self._2_digits_data.to_csv('data/xsmb-2-digits.csv', index=False)
            self._2_digits_data.to_parquet('data/xsmb-2-digits.parquet', index=False)
            print(f"Saved {len(self._2_digits_data)} records to xsmb-2-digits files")
            
        if not self._sparse_data.empty:
            self._sparse_data.to_csv('data/xsmb-sparse.csv', index=False)
            self._sparse_data.to_parquet('data/xsmb-sparse.parquet', index=False)
            print(f"Saved {len(self._sparse_data)} records to xsmb-sparse files")

    def fetch(self, selected_date: date) -> bool:
        url = f'https://xoso.com.vn/xsmb-{selected_date:%d-%m-%Y}.html'
        print(f"Fetching URL: {url}")
        
        try:
            resp = self._http.get(url)
            print(f"Response status: {resp.status_code}")
            
            if resp.status_code != 200:
                return False

            soup = BeautifulSoup(resp.text, 'lxml')
            table = soup.find('table', class_='table-result')
            
            if not table:
                print("Could not find result table")
                return False
                
            prizes = {}
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) != 2:
                    continue
                    
                prize_type = cells[0].get_text(strip=True)
                numbers = cells[1].get_text(strip=True)
                
                if prize_type == 'ĐB':
                    prizes['special'] = int(numbers)
                elif prize_type == '1':
                    prizes['prize1'] = int(numbers)
                elif prize_type == '2':
                    numbers_list = [int(numbers[i:i+5]) for i in range(0, len(numbers), 5)]
                    prizes['prize2_1'] = numbers_list[0]
                    prizes['prize2_2'] = numbers_list[1]
                elif prize_type == '3':
                    numbers_list = [int(numbers[i:i+5]) for i in range(0, len(numbers), 5)]
                    for i, num in enumerate(numbers_list, 1):
                        prizes[f'prize3_{i}'] = num
                elif prize_type == '4':
                    numbers_list = [int(numbers[i:i+4]) for i in range(0, len(numbers), 4)]
                    for i, num in enumerate(numbers_list, 1):
                        prizes[f'prize4_{i}'] = num
                elif prize_type == '5':
                    numbers_list = [int(numbers[i:i+4]) for i in range(0, len(numbers), 4)]
                    for i, num in enumerate(numbers_list, 1):
                        prizes[f'prize5_{i}'] = num
                elif prize_type == '6':
                    numbers_list = [int(numbers[i:i+3]) for i in range(0, len(numbers), 3)]
                    for i, num in enumerate(numbers_list, 1):
                        prizes[f'prize6_{i}'] = num
                elif prize_type == '7':
                    numbers_list = [int(numbers[i:i+2]) for i in range(0, len(numbers), 2)]
                    for i, num in enumerate(numbers_list, 1):
                        prizes[f'prize7_{i}'] = num

            # Create ResultMB object
            result = ResultMB(
                date=selected_date,
                special=prizes['special'],
                prize1=prizes['prize1'],
                prize2_1=prizes['prize2_1'],
                prize2_2=prizes['prize2_2'],
                prize3_1=prizes['prize3_1'],
                prize3_2=prizes['prize3_2'],
                prize3_3=prizes['prize3_3'],
                prize3_4=prizes['prize3_4'],
                prize3_5=prizes['prize3_5'],
                prize3_6=prizes['prize3_6'],
                prize4_1=prizes['prize4_1'],
                prize4_2=prizes['prize4_2'],
                prize4_3=prizes['prize4_3'],
                prize4_4=prizes['prize4_4'],
                prize5_1=prizes['prize5_1'],
                prize5_2=prizes['prize5_2'],
                prize5_3=prizes['prize5_3'],
                prize5_4=prizes['prize5_4'],
                prize5_5=prizes['prize5_5'],
                prize5_6=prizes['prize5_6'],
                prize6_1=prizes['prize6_1'],
                prize6_2=prizes['prize6_2'],
                prize6_3=prizes['prize6_3'],
                prize7_1=prizes['prize7_1'],
                prize7_2=prizes['prize7_2'],
                prize7_3=prizes['prize7_3'],
                prize7_4=prizes['prize7_4']
            )
            
            self._data[result.date] = result
            print(f"Successfully fetched data for {selected_date}")
            return True
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False

    def generate_dataframes(self) -> None:
        if not self._data:
            print("No data to generate dataframes")
            return
            
        # Generate raw dataframe
        self._raw_data = pd.DataFrame([d.model_dump() for d in self._data.values()])
        self._raw_data['date'] = pd.to_datetime(self._raw_data['date'])
        
        # Convert numeric columns to int64
        numeric_columns = self._raw_data.columns.difference(['date'])
        self._raw_data[numeric_columns] = self._raw_data[numeric_columns].astype('int64')
        
        # Generate 2-digits dataframe
        self._2_digits_data = copy(self._raw_data)
        self._2_digits_data[numeric_columns] = self._2_digits_data[numeric_columns].apply(lambda x: x % 100)
        
        # Generate sparse dataframe
        self._sparse_data = pd.concat(
            [
                self._2_digits_data.iloc[:, 0:1],
                pd.DataFrame(np.zeros((self._2_digits_data.shape[0], 100), dtype=int)),
            ],
            axis=1,
        )
        
        print(f"Generated dataframes with data from {min(self._data.keys())} to {max(self._data.keys())}")
