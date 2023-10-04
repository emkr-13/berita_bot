import feedparser
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from decouple import config
from telegram import ChatAction
import time
import logging

from cek_berita import *
conn = get_db_connection()

# Konfigurasi Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = config('API_KEY')

# List berita yang ada 
RSS_FEED_URLS = ['https://www.suara.com/rss/news',
                 'https://www.vice.com/id/rss?locale=id_id', 
                 'https://www.cnnindonesia.com/nasional/rss', 
                 'https://www.cnbcindonesia.com/news/rss', 
                 'https://www.republika.co.id/rss',
                 'https://lapi.kumparan.com/v2.0/rss/',
                 'https://www.merdeka.com/feed',
                 'https://www.viva.co.id/get/all',
                 'https://www.sindonews.com/feed',
                 'https://wartakota.tribunnews.com/rss',
                 'https://www.jpnn.com/index.php?mib=rss',
                 'https://www.inews.id/feed/news',
                 'https://www.tribunnews.com/rss',
                 'https://nasional.sindonews.com/rss']

CHECK_INTERVAL = int(config('TIME_CHECKS'))

bot = telegram.Bot(token=API_KEY)
# Tambah Keywords filter
filter = ["ganjar", "anies", "prabowo"]

def fetch_latest_news():
    all_news_entries = []
    for url in RSS_FEED_URLS:
        try:
            feed = feedparser.parse(url)
            # Pengecekan apakah feed memiliki judul dan tautan (bukan bot)
            if 'title' in feed.feed and 'link' in feed.feed:
                all_news_entries.extend(feed.entries)
                logger.info(f"Fetched news from {url}")
        except Exception as e:
            logger.error(f"Failed to fetch news from {url}. Error: {str(e)}")
    
    all_news_entries.sort(key=lambda x: x.published_parsed, reverse=True)
    return all_news_entries





def send_news_updates(context: CallbackContext):
    chat_id = context.job.context
    news_entries = fetch_latest_news()
    
    if news_entries:
        for latest_news in news_entries:
            title = latest_news.title
            link = latest_news.link

            # Check if the title contains any of the keywords from the filter list
            if any(keyword in title.lower() for keyword in filter):
                message = f'<b>{title}</b>\n<a href="{link}">Read more</a>'
                if not is_news_exists(title,conn):
                    try:
                        context.bot.send_message(chat_id=chat_id, text=message, parse_mode=telegram.ParseMode.HTML)
                        logger.info(f"Sent news update to group chat {chat_id}: {title}")
                        insert_news_data(title, link, conn)  # Menambahkan tanggal publikasi ke dalam database
                    except Exception as e:
                        if "Flood control exceeded" in str(e):
                            logger.warning("Flood control exceeded. Retrying in 60 seconds...")
                            time.sleep(60)
                            continue
                        else:
                            logger.error(f"Failed to send news update to group chat {chat_id}: {title}. Error: {str(e)}")
                

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome! Use the /news command to get the latest news.')


def news(update: Update, context: CallbackContext):
    news_entries = fetch_latest_news()
    if news_entries:
        latest_news = news_entries[0]
        title = latest_news.title
        link = latest_news.link
        pub_date = latest_news.pubDate
        message = f'<b>{title}</b>\n<a href="{link}">Read more</a>\n Tanggal: {pub_date}'
        try:
            update.message.reply_text(message, parse_mode=telegram.ParseMode.HTML)
            logger.info("Sent news update to user")
        except Exception as e:
            logger.error(f"Failed to send news update to user. Error: {str(e)}")
    else:
        update.message.reply_text('No news available at the moment.')
        logger.info("User requested news, but no news available")

def error(update, context):
    if update and update.message:
        if 'Forbidden: bot can\'t send messages to bots' in str(context.error):
            logger.warning(f'Bot is trying to send a message to another bot. Ignoring.')
        else:
            logger.warning(f'Update "{update}" caused error "{context.error}"')



if __name__ == '__main__':
    updater = Updater(API_KEY, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('news', news))

    # Error handler
    dp.add_error_handler(error)

    # Replace 'YOUR_GROUP_CHAT_ID' with the actual chat ID of your group
    group_chat_id = int(config('GRUP_CHAT_ID'))

    # Job queue for sending news updates automatically
    job_queue = updater.job_queue
    job_queue.run_repeating(send_news_updates, interval=CHECK_INTERVAL, context=group_chat_id)


    # Start the bot
    updater.start_polling()
    updater.idle()
