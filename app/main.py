import logging
import time
import pandas as pd
from typing import List
from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UAS Cloud Observability App")

# Templates
templates = Jinja2Templates(directory="app/templates")

# --- Prometheus Metrics ---
# 1. Counter: Total CSV files uploaded/processed
CSV_UPLOAD_TOTAL = Counter(
    "app_csv_upload_total", 
    "Total number of CSV files uploaded",
    ["status"] # success, error
)

# 2. Counter: Total rows processed
CSV_ROWS_PROCESSED = Counter(
    "app_csv_rows_processed_total",
    "Total number of CSV rows processed"
)

# 3. Histogram: Time taken to process a CSV file
CSV_PROCESSING_TIME = Histogram(
    "app_csv_processing_seconds",
    "Time taken to process CSV file (parsing + analytics)",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# 4. Gauge: Last recorded revenue from a batch
LAST_BATCH_REVENUE = Gauge(
    "app_last_batch_revenue_total",
    "Total revenue calculated from the last processed batch"
)

# 5. Counter: Application logic errors
APP_ERRORS_TOTAL = Counter(
    "app_logic_errors_total",
    "Total number of application logic errors",
    ["type"]
)

# Instrument the app (Default metrics: http requests, latency, etc.)
Instrumentator().instrument(app).expose(app)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main upload page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_csv(request: Request, file: UploadFile = File(...)):
    """Handle CSV upload and process analytics."""
    start_time = time.time()
    
    if not file.filename.endswith('.csv'):
        APP_ERRORS_TOTAL.labels(type="invalid_file_extension").inc()
        CSV_UPLOAD_TOTAL.labels(status="error").inc()
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": "Invalid file type. Please upload a CSV file."
        })

    try:
        # Read CSV into Pandas DataFrame
        df = pd.read_csv(file.file)
        
        # Validation: Check required columns
        required_columns = {'transaction_id', 'product', 'category', 'price', 'quantity', 'timestamp'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            error_msg = f"Missing required columns: {', '.join(missing)}"
            logger.error(error_msg)
            
            APP_ERRORS_TOTAL.labels(type="missing_columns").inc()
            CSV_UPLOAD_TOTAL.labels(status="error").inc()
            
            return templates.TemplateResponse("index.html", {
                "request": request, 
                "error": error_msg
            })

        # --- Analytics Computation ---
        
        # 1. Total Transactions
        total_transactions = len(df)
        
        # 2. Total Revenue
        df['revenue'] = df['price'] * df['quantity']
        total_revenue = df['revenue'].sum()
        
        # 3. Revenue per Category
        revenue_per_category = df.groupby('category')['revenue'].sum().reset_index()
        revenue_per_category_dict = revenue_per_category.to_dict(orient='records')
        
        # 4. Average Order Value (AOV)
        aov = total_revenue / total_transactions if total_transactions > 0 else 0

        # --- Update Metrics ---
        CSV_ROWS_PROCESSED.inc(total_transactions)
        LAST_BATCH_REVENUE.set(total_revenue)
        CSV_UPLOAD_TOTAL.labels(status="success").inc()
        
        # Record processing time
        duration = time.time() - start_time
        CSV_PROCESSING_TIME.observe(duration)
        
        logger.info(f"Processed {total_transactions} transactions. Revenue: {total_revenue}")

        return templates.TemplateResponse("index.html", {
            "request": request,
            "result": True,
            "total_transactions": total_transactions,
            "total_revenue": f"{total_revenue:,.2f}",
            "aov": f"{aov:,.2f}",
            "revenue_by_category": revenue_per_category_dict,
            "processing_time": f"{duration:.4f}"
        })

    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        APP_ERRORS_TOTAL.labels(type="processing_exception").inc()
        CSV_UPLOAD_TOTAL.labels(status="error").inc()
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"Error processing file: {str(e)}"
        })

@app.post("/simulate-error")
async def simulate_error():
    """Endpoint to intentionally trigger 500 error for monitoring."""
    APP_ERRORS_TOTAL.labels(type="manual_trigger").inc()
    raise Exception("Manually triggered exception for testing monitoring!")
