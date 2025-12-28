# UAS Cloud - Observable Web Application

This is a containerized web application designed for the Cloud Services UAS project. It demonstrates backend processing, system observability, and monitoring using the Prometheus/Grafana stack.

## Architecture

*   **Web App**: FastAPI (Python) + HTML/TailwindCSS (UI)
*   **Database**: None (state is transient per request, metrics are persistent in memory/Prometheus)
*   **Monitoring**:
    *   **Prometheus**: Metrics collection
    *   **Grafana**: Metrics visualization
    *   **Node Exporter**: Host hardware metrics
    *   **cAdvisor**: Container runtime metrics

## Prerequisites

*   Docker Desktop
*   Git

## How to Run

1.  Clone this repository (if not already done).
2.  Navigate to the project root.
3.  Start the stack:
    ```bash
    docker compose build
    docker compose up
    ```
4.  Wait for all services to start (you will see logs from `uas_webapp`, `uas_prometheus`, etc.).

## Usage

### 1. Web Application (Workload Generator)
*   **URL**: [http://localhost:8000](http://localhost:8000)
*   **Action**:
    *   Download or use the provided `sample_data.csv`.
    *   Upload it using the "Choose File" button.
    *   Click "Analyze Data" to trigger backend processing.
*   **Result**: You will see a summary of revenue, transactions, and category breakdown. **Refresh the page or upload multiple times to generate load.**

### 2. Metrics Endpoint
*   **URL**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
*   **Description**: Raw Prometheus metrics exposed by the application.

### 3. Prometheus (Data Source)
*   **URL**: [http://localhost:9090](http://localhost:9090)
*   **Action**: You can query metrics here.
    *   Example Query: `app_csv_rows_processed_total`

### 4. Grafana (Dashboards)
*   **URL**: [http://localhost:3000](http://localhost:3000)
    *   **Username**: `admin`
    *   **Password**: `admin` (skip change password if prompted)
*   **Setup Dashboard**:
    1.  Go to **Connections** > **Data Sources** > **Add data source** > **Prometheus**.
    2.  Set URL to `http://prometheus:9090` (internal Docker DNS).
    3.  Click **Save & Test**.
    4.  Go to **Dashboards** > **New** > **Import**.
    5.  Click **Upload dashboard JSON file** and select `grafana/dashboard.json` from the project folder.
    6.  Select the **Prometheus** data source you just created.
    7.  Click **Import**.
    8.  You should now see the "UAS Cloud Observability Dashboard" with metrics.

## Exposed Metrics

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `app_csv_upload_total` | Counter | Total CSV files uploaded (labels: `status`) |
| `app_csv_rows_processed_total` | Counter | Total rows of data processed |
| `app_csv_processing_seconds` | Histogram | Time taken to process analytics |
| `app_logic_errors_total` | Counter | Application errors (labels: `type`) |
| `process_cpu_seconds_total` | Counter | CPU usage of the Python process |

## Troubleshooting

*   **Port Conflicts**: Ensure ports 8000, 9090, 3000, 9100 are free.
*   **Docker Memory**: Ensure Docker Desktop has enough memory (2GB+) allocated.
