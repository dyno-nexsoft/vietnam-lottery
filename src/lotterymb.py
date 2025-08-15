import logging
from copy import copy
from datetime import date
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from .lottery_base import LotteryBase
from .models.lottery_mb import ResultMB, ResultMBList

logger = logging.getLogger('vietnam-lottery')


class LotteryMB(LotteryBase):
    def __init__(self) -> None:
        super().__init__('xsmb', ResultMB, ResultMBList)

    def fetch(self, selected_date: date) -> ResultMB | None:
        url = f'https://xoso.com.vn/xsmb-{selected_date:%d-%m-%Y}.html'
        logger.info(f"Fetching URL: {url}")
        
        try:
            resp = self._http.get(url)
            logger.info(f"Response status: {resp.status_code}")
            
            if resp.status_code != 200:
                logger.error(f"Failed to fetch URL {url}, status code: {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, 'lxml')
            table = soup.find('table', class_='table-result')
            
            if not table:
                logger.error("Could not find result table")
                return None
                
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
            
            self._data[result.date] = result # Update internal data store
            logger.info(f"Successfully fetched data for {selected_date}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching data for {selected_date}: {e}")
            return None

    def generate_dataframes(self) -> None:
        if not self._data:
            logger.info("No data to generate dataframes")
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
        
        logger.info(f"Generated dataframes with data from {min(self._data.keys())} to {max(self._data.keys())}")