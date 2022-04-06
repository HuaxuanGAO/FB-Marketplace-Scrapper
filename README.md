# Requirements
- pymysql
- selenium

# How to run
- Install dependencies
- Modify `config.py` to fill in the DB host, username, password
- Modify `config.py` to fill in the Facebook accounts details (need to login to see products)
  - The format should be `ACCOUNTS=[(EMAIL1, PASS1), (EMAIL2, PASS2), ...]`
- Create the DB database and tables defined in the schemas.txt
- Get product links: python scrape_links.py
- Get product details: python scrape_details.py

# Note
Some of the xpaths used in this project are based on dynamically generated class names.
Therefore it is not stable. 
Update the xpaths when you encounter problem.
