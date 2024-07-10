from google.cloud import bigquery
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.bigquery import BigQuery
from mage_ai.io.config import ConfigFileLoader
from os import path, environ
import pandas as pd



# Define your schemas here
schemas = {
    'vehicle_data': [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("deviceId", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("speed", "FLOAT"),
        bigquery.SchemaField("direction", "STRING"),
        bigquery.SchemaField("make", "STRING"),
        bigquery.SchemaField("model", "STRING"),
        bigquery.SchemaField("year", "INTEGER"),
    ],
    'gps_data': [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("deviceId", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("vehicleType", "STRING"),
        bigquery.SchemaField("location", "STRING"),
    ],
    'weather_data': [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("deviceId", "STRING"),
        bigquery.SchemaField("location", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("temperature", "FLOAT"),
        bigquery.SchemaField("weatherCondition", "STRING"),
        bigquery.SchemaField("precipitation", "FLOAT"),
        bigquery.SchemaField("humidity", "FLOAT"),
        bigquery.SchemaField("windSpeed", "FLOAT"),
    ]
}

config_path = path.join(get_repo_path(), 'io_config.yaml')
config_profile = 'default'

@data_exporter
def export_data_to_bigquery(data: dict):
    """
    Export data from a dictionary to BigQuery creating new tables for each key.
    """
    bq_client = bigquery.Client()

    for key, dataframes in data.items():
        if key not in schemas:
            raise ValueError(f"Unknown key: {key}")
        
        # Ensure all elements in dataframes are DataFrames
        converted_dataframes = []
        for i, df in enumerate(dataframes):
            if not isinstance(df, pd.DataFrame):
                print(f"Converting element at index {i} in dataframes for key '{key}' from {type(df)} to DataFrame")
                df = pd.DataFrame(df)
            converted_dataframes.append(df)

        # Concatenate all dataframes for the key
        df = pd.concat(converted_dataframes, ignore_index=True)
        
        # Ensure column names are strings
        df.columns = df.columns.astype(str)
        
        schema = schemas[key]
        table_id = f'vehicle-tracking-system-427015.my_dataset.{key}'

        # Create the BigQuery table if it doesn't exist
        table_ref = bigquery.Table(table_id, schema=schema)
        try:
            bq_client.create_table(table_ref)
            print(f"Table {table_id} created successfully.")
        except Exception as e:
            print(f"Error creating table {table_id}: {str(e)}")

        # Export data to BigQuery table
        BigQuery.with_config(ConfigFileLoader(config_path, config_profile)).export(
            df,
            table_id,
            if_exists='replace',  # Specify resolution policy if table name already exists
        )