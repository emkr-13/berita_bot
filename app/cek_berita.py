import psycopg2
from decouple import config
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a function to establish a database connection
def get_db_connection():
    try:
        # Konfigurasi koneksi ke database
        db_host = config('POSTGRE_DB_HOST')
        db_port = config('POSTGRE_DB_PORT')
        db_name = config('POSTGRE_DB_NAME')
        db_user = config('POSTGRE_DB_USER')
        db_pass = config('POSTGRE_DB_PASS')

        # Membuat koneksi ke database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to establish a database connection. Error: {str(e)}")
        return None

def insert_news_data(title, link, conn):
    try:
        # Membuat kursor untuk eksekusi perintah SQL
        cursor = conn.cursor()

        # Perintah SQL untuk memasukkan data ke dalam tabel "berita"
        insert_query = "INSERT INTO berita (judul_berita, link) VALUES (%s, %s)"
        cursor.execute(insert_query, (title, link))

        # Commit perubahan ke database
        conn.commit()

        # Menutup kursor
        cursor.close()

        logger.info(f"Inserted news into database: {title}")

    except Exception as e:
        logger.error(f"Failed to insert news into database. Error: {str(e)}")

def is_news_exists(title, conn):
    try:
        # Membuat kursor untuk eksekusi perintah SQL
        cursor = conn.cursor()

        # Perintah SQL untuk memeriksa apakah berita dengan judul yang sama sudah ada dalam database
        cursor.execute("SELECT COUNT(*) FROM berita WHERE judul_berita = %s", (title,))
        count = cursor.fetchone()[0]

        # Menutup kursor
        cursor.close()

        # Mengembalikan True jika berita sudah ada, False jika tidak
        return count > 0

    except Exception as e:
        logger.error(f"Failed to check if news exists in the database. Error: {str(e)}")
        return False