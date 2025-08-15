import argparse
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional
import json
import os
from lotterymb import LotteryMB
from lotterymn import LotteryMN
from lotterymt import LotteryMT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lottery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vietnam-lottery')


def fetch_xsmb(start_date: date, end_date: date) -> bool:
    logger.info(f"Fetching XSMB from {start_date} to {end_date}")
    try:
        lottery = LotteryMB()
        lottery.load()
        
        delta = (end_date - start_date).days + 1
        success_count = 0
        
        for i in range(delta):
            selected_date = start_date + timedelta(days=i)
            try:
                logger.info(f'Fetching XSMB: {selected_date}')
                result = lottery.fetch(selected_date)
                if validate_lottery_data(result, "XSMB"):
                    success_count += 1
                else:
                    logger.warning(f"Invalid data for XSMB on {selected_date}")
            except Exception as e:
                logger.error(f"Error fetching XSMB for {selected_date}: {str(e)}")

        if success_count > 0:
            lottery.generate_dataframes()
            lottery.dump()
            logger.info(f"Successfully fetched {success_count}/{delta} days of XSMB data")
            return True
        else:
            logger.error("No valid XSMB data fetched")
            return False
            
    except Exception as e:
        logger.error(f"Error in XSMB fetch process: {str(e)}")
        return False


def fetch_xsmn(start_date: date, end_date: date) -> bool:
    logger.info(f"Fetching XSMN from {start_date} to {end_date}")
    try:
        lottery = LotteryMN()
        lottery.load()
        
        delta = (end_date - start_date).days + 1
        success_count = 0
        
        for i in range(delta):
            selected_date = start_date + timedelta(days=i)
            try:
                logger.info(f'Fetching XSMN: {selected_date}')
                result = lottery.fetch(selected_date)
                if validate_lottery_data(result, "XSMN"):
                    success_count += 1
                else:
                    logger.warning(f"Invalid data for XSMN on {selected_date}")
            except Exception as e:
                logger.error(f"Error fetching XSMN for {selected_date}: {str(e)}")

        if success_count > 0:
            lottery.generate_dataframes()
            lottery.dump()
            logger.info(f"Successfully fetched {success_count}/{delta} days of XSMN data")
            return True
        else:
            logger.error("No valid XSMN data fetched")
            return False
            
    except Exception as e:
        logger.error(f"Error in XSMN fetch process: {str(e)}")
        return False


def fetch_xsmt(start_date: date, end_date: date) -> bool:
    logger.info(f"Fetching XSMT from {start_date} to {end_date}")
    try:
        lottery = LotteryMT()
        lottery.load()
        
        delta = (end_date - start_date).days + 1
        success_count = 0
        
        for i in range(delta):
            selected_date = start_date + timedelta(days=i)
            try:
                logger.info(f'Fetching XSMT: {selected_date}')
                result = lottery.fetch(selected_date)
                if validate_lottery_data(result, "XSMT"):
                    success_count += 1
                else:
                    logger.warning(f"Invalid data for XSMT on {selected_date}")
            except Exception as e:
                logger.error(f"Error fetching XSMT for {selected_date}: {str(e)}")

        if success_count > 0:
            lottery.generate_dataframes()
            lottery.dump()
            logger.info(f"Successfully fetched {success_count}/{delta} days of XSMT data")
            return True
        else:
            logger.error("No valid XSMT data fetched")
            return False
            
    except Exception as e:
        logger.error(f"Error in XSMT fetch process: {str(e)}")
        return False


def parse_date(date_str: str) -> date:
    """Parse date string in format YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date format: {e}. Use YYYY-MM-DD")

def validate_lottery_data(data: any, lottery_type: str) -> bool:
    """Validate lottery data structure and content"""
    if data is None:
        logger.error(f"Empty data for {lottery_type}")
        return False
    
    try:
        # For now just check if we got any data back
        # The actual validation is handled by Pydantic models in the lottery classes
        return True
    except Exception as e:
        logger.error(f"Error validating {lottery_type} data: {str(e)}")
        return False

def send_notification(message: str, error: bool = False) -> None:
    """Send notification about job status"""
    # Check if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id:
        try:
            import requests
            level = "❌ ERROR" if error else "✅ INFO"
            text = f"{level}: {message}"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text})
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")

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
        
        # Fetch all three regions
        success = {
            'XSMB': fetch_xsmb(start_date, end_date),
            'XSMN': fetch_xsmn(start_date, end_date),
            'XSMT': fetch_xsmt(start_date, end_date)
        }
        
        # Log summary
        summary = []
        for region, status in success.items():
            result = "succeeded" if status else "failed"
            summary.append(f"{region}: {result}")
        
        summary_msg = "Lottery Data Fetch Summary:\n" + "\n".join(summary)
        logger.info(summary_msg)
        
        # Send notification
        if all(success.values()):
            send_notification(f"Successfully fetched all lottery data for {end_date}")
        else:
            failed_regions = [region for region, status in success.items() if not status]
            send_notification(
                f"Failed to fetch data for {', '.join(failed_regions)} on {end_date}",
                error=True
            )
        
    except Exception as e:
        error_msg = f"Critical error in lottery fetch process: {str(e)}"
        logger.error(error_msg)
        send_notification(error_msg, error=True)
