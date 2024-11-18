import requests
import time
import pandas as pd
from datetime import datetime

from airflow.decorators import dag, task
from airflow.utils.task_group import TaskGroup
from airflow.operators.bash import BashOperator
from airflow.models import Variable

# Define the base URL and parameters
BASE_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
NUM = 100  # Number of cards per request
DELAY_BETWEEN_REQUESTS = 0.1  # 100ms delay to respect API rate limit
TOTAL_CARDS = 5000


@dag(
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['DE_PROJECT4'],
)
def yugioh_pipeline():

    @task()
    def fetch_yugioh_data():
        all_cards = []
        offset = 0
        while offset < TOTAL_CARDS:
            params = {
                "num": NUM,
                "offset": offset,
                "misc": "yes"
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            if 'data' not in data or len(data['data']) == 0:
                break
            all_cards.extend(data['data'])
            offset += NUM
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # Convert the card data into a pandas DataFrame
        df = pd.DataFrame(all_cards)
        
        # Return the DataFrame as a JSON string to pass it to the next task
        return df.to_json(orient="records", lines=True)
    
    with TaskGroup("create_azure_resource", tooltip="Tasks for Terraform operations") as terraform_group:

        # Initialize Terraform
        terraform_init = BashOperator(
            task_id="terraform_init",
            bash_command="terraform -chdir=/usr/local/airflow/include/terraform init"
        )

        # Apply Terraform
        terraform_apply = BashOperator(
            task_id="terraform_apply",
            bash_command="terraform -chdir=/usr/local/airflow/include/terraform apply -auto-approve"
        )

        # Get Storage Access Key
        get_access_key = BashOperator(
            task_id="get_access_key",
            bash_command="""
            ACCESS_KEY=$(terraform -chdir=/usr/local/airflow/include/terraform output -raw adls_access_key)
            airflow variables set ACCESS_KEY $ACCESS_KEY
            """,
        )

        # Define dependencies within the TaskGroup
        terraform_init >> terraform_apply >> get_access_key

    @task()
    def upload_to_adls(data):
        # Convert the JSON string back to DataFrame
        df = pd.read_json(data, orient="records", lines=True)

        # Save DataFrame directly to ADLS
        adls_path = "abfs://yugioh-data@yugiohprojectstorage.dfs.core.windows.net/raw-data/yugioh_cards.json"
        
        # Use the adlfs library to write the DataFrame to ADLS
        df.to_json(adls_path, 
                   storage_options={
                       'account_key': Variable.get('ACCESS_KEY')
                   },
                   orient="records", 
                   lines=True)

    # Define the task dependencies
    data = fetch_yugioh_data()
    terraform_group >> data >> upload_to_adls(data)

yugioh_dag = yugioh_pipeline()
