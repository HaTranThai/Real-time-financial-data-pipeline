# Real-time Financial Market Data Pipeline

![System Architecture](https://github.com/HaTranThai/Real-time-financial-data-pipeline/blob/main/image/%E1%BA%A2nh%20ch%E1%BB%A5p%20m%C3%A0n%20h%C3%ACnh%202024-08-18%20163248.png)

## Getting Started

1. Clone the repository:
    ```bash
    git clone https://github.com/HaTranThai/Real-time-financial-data-pipeline.git
    ```
2. Navigate to the project directory:
    ```bash
    cd Real-time-financial-data-pipeline
    ```
3. Run Docker Compose to spin up the services:
    ```bash
    docker-compose up -d
    ```
4. Run the spark_stream.py file to get data from kafka and put that data into cassandra:
    ```bash
    python spark_stream.py
    ```
5. Run the file sma.py:
   ```bash
   python sma.py
   ```
 ### Visualization with Grafana


 
