# from django.core.management.base import BaseCommand
# from zodiac.utils import generate_daily_predictions
# from datetime import date

# class Command(BaseCommand):
#     help = "Generate daily zodiac predictions for all 12 signs and store in DB."

#     def add_arguments(self, parser):
#         parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD (optional).")
#         parser.add_argument("--force", action="store_true", help="Regenerate even if exists.")

#     def handle(self, *args, **options):
#         date_str = options.get("date")
#         if date_str:
#             import datetime
#             date_value = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
#         else:
#             date_value = date.today()

#         force = options.get("force", False)
#         results = generate_daily_predictions(date_value=date_value, force=force)
#         self.stdout.write(self.style.SUCCESS(f"Generated {len(results)} predictions for {date_value}"))
