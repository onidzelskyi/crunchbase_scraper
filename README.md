# crunchbase_scraper
Scrape companies funding info from crunchbase site

Installation
==

```bash
# Install headless mode
sudo apt install xvfb

# Download chromedriver zip archive
wget -N http://chromedriver.storage.googleapis.com/2.20/chromedriver_linux64.zip

# Extract archive
unzip chromedriver_linux64.zip

# Make module executable
chmod +x ./chromedriver

# Add current path with chromedirver to PATH
export PATH=$pwd:$PATH
```

```bash
mkvirtualenv -p python3.5 crunchbase_scraper
```

```bash
pip install -r requirements.txt
```

Tests
==

```bash
python -m unittest test_db_model
```

