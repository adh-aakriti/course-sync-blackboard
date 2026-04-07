import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient


URL = "http://books.toscrape.com/"

response = requests.get(URL)

print(response.content)

soup = None  # Replace this


# TODO: Find all book containers
books = None  # Replace this


book_data = []

for book in books:
    # TODO: Extract title
    title = None

    # TODO: Extract price
    price = None

    # TODO: Extract availability
    availability = None

    structured_book = {
        "title": title,
        "price": price,
        "availability": availability
    }

    book_data.append(structured_book)


print(f"Scraped {len(book_data)} books")


# ==============================
# STEP 2: CONNECT TO MONGODB
# ==============================

# If local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# If using Atlas, replace the string above


db = client["web_scraping_db"]
collection = db["books"]


# ==============================
# STEP 3: INSERT DATA
# ==============================

# TODO: Insert all books into MongoDB



print("Data inserted successfully!")


# ==============================
# STEP 4: QUERY DATA
# ==============================

print("\nSample documents from MongoDB:\n")

# TODO: Retrieve and print 5 documents from the collection


