# india_time.py
# Gets the current time in India (IST, UTC+5:30)

from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

now_ist = datetime.now(IST)

print("Current time in India:")
print(now_ist.strftime("%A, %d %B %Y"))
print(now_ist.strftime("%I:%M:%S %p") + " IST")
