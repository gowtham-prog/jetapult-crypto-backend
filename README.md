## **Backend: Django API + Chat Assistant**

### **Overview**

The backend provides API endpoints to fetch cryptocurrency data, store historical prices, manage favorites, and serve a simple rule-based chat assistant.

### **Features**

* Top N cryptocurrencies endpoint (price, volume, % change).
* Historical price trends endpoint (last 30 days).
* Rule-based Q&A endpoint for queries like:
  * “What is the price of Bitcoin?”
  * “Show me the 7-day trend of Ethereum.”
* Favorites management (requires authentication).
* Deployed on Google Cloud Platform with Gunicorn, Supervisor, and Nginx.


## **Assumptions & Limitations**

* Chat assistant is rule-based; not AI-powered.
* Historical data is limited to 30 days.
* Favorites require authentication.
* Frontend and backend must be running simultaneously for full functionality.
* History of every coins will be fetched once in a day, will have atmost 60 seconds latency because of rate-limiting on CoinGecko

## **Chat Assistant LLD**
* Regex classification → Identify if query is price-related, trend-related, or unknown.
* Coin resolution → Match coin name or symbol from user input against DB.
* Structured output → Return dictionaries with "type", "coin", "answer", and "data" so the frontend/chatbot can format the response nicely.
* Fallback help → If no match, provide guidance on how to use the feature.

### **Tech Stack**

* **Framework:** Django 5 (Python 3.12)
* **Database:** SQlite
* **Task Queue:** Celery + Celery Beat
* **Cache/Broker:** Redis
* **API Integration:** CoinGecko Demo APIs
* **Deployment:** GCP, Gunicorn, Supervisor, Nginx

### **Setup & Run Locally**

1. Clone the repository:

```bash
git clone https://github.com/gowtham-prog/jetapult-crypto-backend.git
cd backend
```

2. Create a virtual environment and activate:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables:

```bash
COINGECKO_APIKEY=YOUR_COINGECKO_APIKEY
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Start Django development server:

```bash
python manage.py runserver
```

7. Ensure You have redis server


### **macOS**

1. **Install Redis** (if not already):

   ```bash
   brew install redis
   ```
2. **Start Redis server manually**:

   ```bash
   redis-server
   ```

   This will run in the foreground.
3. **Start Redis server in background (service mode)**:

   ```bash
   brew services start redis
   ```

   To stop:

   ```bash
   brew services stop redis
   ```

---

### **Linux (Ubuntu/Debian example)**

1. **Install Redis**:

   ```bash
   sudo apt update
   sudo apt install redis-server -y
   ```
2. **Start Redis server manually**:

   ```bash
   redis-server
   ```
3. **Run as a systemd service**:

   ```bash
   sudo systemctl start redis-server
   sudo systemctl enable redis-server   # auto-start on boot
   ```

   To check status:

   ```bash
   sudo systemctl status redis-server
   ```

---

### **Windows**

Redis doesn’t officially support Windows anymore, but you can still run it in these ways:

1. **Via WSL (recommended)**:

   * Install WSL2 (Windows Subsystem for Linux).
   * Inside Ubuntu (or another distro), follow the Linux steps above.

2. **Using Memurai (Redis-compatible server for Windows)**:

   * Download from [https://www.memurai.com](https://www.memurai.com).
   * Install and run as a service.

3. **Docker (cross-platform)**:

   ```powershell
   docker run --name redis -p 6379:6379 -d redis
   ```

---

✅ After starting Redis on any platform, test it with:

```bash
redis-cli ping
```

You should get back:

```
PONG
```



8. Start Celery worker and beat (in separate terminals):

```bash
celery -A jetapult_crypto_backend worker -l INFO --concurrency=1
celery -A jetapult_crypto_backend beat -l INFO 
```

8. The API will be available at `http://localhost:8000`.

### **Deployment Notes**

* Gunicorn serves the Django app.
* Supervisor ensures Gunicorn is running in the background.
* Nginx acts as a reverse proxy for static files and API routing.
* Celery + Redis handle background tasks and caching.

### **Deployed Link**

[Backend API Live](https://alludu.duckdns.org/)

---

