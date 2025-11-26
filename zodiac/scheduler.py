# zodiac/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_job, register_events
from zodiac.utils import generate_daily_predictions
from datetime import date
import logging

logger = logging.getLogger(__name__)

def start():
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    @register_job(scheduler, "cron", hour=11, minute=1)  
    def daily_prediction_job():
        try:
            logger.info(f"Start Generated Today's Zodiac")
            results = generate_daily_predictions(date_value=date.today())
            logger.info(f"✅ Generated {len(results)} predictions for {date.today()}")
        except Exception as e:
            logger.error(f"❌ Error in daily prediction job: {str(e)}")

    register_events(scheduler)
    scheduler.start()
    logger.info("🌅 Zodiac APScheduler started successfully.") 
 