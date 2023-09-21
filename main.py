import threading
import time
from datetime import datetime

import schedule
import scheduler # noqa

from bot_core import bot
import handlers  # noqa
from misc import BOT_NAME

if __name__ == '__main__':
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    print(f"Start {BOT_NAME} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
    while True:
        schedule.run_pending()
        time.sleep(5)

# python -m pipreqs.pipreqs --encoding UTF8 --force
