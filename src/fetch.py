import argparse
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
import json

from .lotterymb import LotteryMB
from .lotterymn import LotteryMN
from .lotterymt import LotteryMT
from .lottery_base import LotteryBase # Import LotteryBase for type hinting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lottery.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vietnam-lottery')


def _fetch_lottery_data(lottery_instance: LotteryBase, lottery_type: str, start_date: date, end_date: date) -> bool:
    logger.info(f"Fetching {lottery_type} from {start_date} to {end_date}")
    try:
        lottery_instance.load()
        
        delta = (end_date - start_date).days + 1
        success_count = 0
        
        for i in range(delta):
            selected_date = start_date + timedelta(days=i)
            
            if selected_date in lottery_instance._data:
                logger.info(f"Data for {lottery_type} on {selected_date} already exists. Skipping fetch.")
                success_count += 1 # Count as successful since data is already there
                continue

            try:
                logger.info(f'Fetching {lottery_type}: {selected_date}')
                result = lottery_instance.fetch(selected_date)
                if result is not None: # Assuming fetch returns None on failure
                    success_count += 1
                else:
                    logger.warning(f"No data or invalid data for {lottery_type} on {selected_date}")
            except Exception as e:
                logger.error(f"Error fetching {lottery_type} for {selected_date}: {str(e)}")

        if success_count > 0:
            lottery_instance.generate_dataframes()
            lottery_instance.dump()
            lottery_instance.generate_and_dump_sparse_json()
            logger.info(f"Successfully fetched {success_count}/{delta} days of {lottery_type} data")
            return True
        else:
            logger.error(f"No valid {lottery_type} data fetched")
            return False
            
    except Exception as e:
        logger.error(f"Error in {lottery_type} fetch process: {str(e)}")
        return False


def parse_date(date_str: str) -> date:
    """Parse date string in format YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date format: {e}. Use YYYY-MM-DD")

def get_date_range(start_date: date = None, end_date: date = None) -> tuple[date, date]:
    """Get start and end dates based on input or current time"""
    if end_date is None:
        tz = ZoneInfo('Asia/Ho_Chi_Minh')
        now = datetime.now(tz)
        end_date = now.date()
        
        # Adjust end date based on lottery result times
        current_time = now.time()
        logger.info(f"Current time in Vietnam: {current_time}")
        
        if current_time < time(16, 35):  # Before XSMN
            logger.info("Before XSMN time, using previous day's data")
            end_date -= timedelta(days=1)
        elif current_time < time(17, 35):  # Before XSMT
            logger.info("Can fetch XSMN but not XSMT/XSMB")
            pass
        elif current_time < time(18, 35):  # Before XSMB
            logger.info("Can fetch XSMN and XSMT but not XSMB")
            pass
    
    if start_date is None:
        # Start from 7 days ago by default
        start_date = end_date - timedelta(days=7)
    
    logger.info(f"Date range: {start_date} to {end_date}")
    return start_date, end_date


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Fetch lottery results for all regions')
        parser.add_argument('--start', type=parse_date, help='Start date in format YYYY-MM-DD')
        parser.add_argument('--end', type=parse_date, help='End date in format YYYY-MM-DD')
        
        args = parser.parse_args()
        start_date, end_date = get_date_range(args.start, args.end)
        
        if start_date > end_date:
            parser.error("Start date cannot be after end date")
        
        # Fetch all three regions using the generic function
        success = {
            'XSMB': _fetch_lottery_data(LotteryMB(), 'XSMB', start_date, end_date),
            'XSMN': _fetch_lottery_data(LotteryMN(), 'XSMN', start_date, end_date),
            'XSMT': _fetch_lottery_data(LotteryMT(), 'XSMT', start_date, end_date)
        }
        
        # Log summary
        summary = []
        for region, status in success.items():
            result = "succeeded" if status else "failed"
            summary.append(f"{region}: {result}")
        
        summary_msg = "Lottery Data Fetch Summary:\n" + "\n".join(summary)
        logger.info(summary_msg)
        
    except Exception as e:
        error_msg = f"Critical error in lottery fetch process: {str(e)}"
        logger.error(error_msg)