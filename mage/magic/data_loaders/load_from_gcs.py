from google.cloud import storage
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.google_cloud_storage import GoogleCloudStorage
from os import path, environ
import os

# Ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keyfile.json'

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader


@data_loader
def load_all_from_google_cloud_storage(*args, **kwargs):
    """
    Template for loading all parquet files from multiple directories in a Google Cloud Storage bucket.
    Specify your configuration settings in 'io_config.yaml'.
    """
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    bucket_name = 'bucket_name'
    directories = ['spark_checkpoint/vehicle_data', 'spark_checkpoint/weather_data', 'spark_checkpoint/gps_data']

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)

    all_data = {}

    for directory in directories:
        blobs = bucket.list_blobs(prefix=directory)
        dataframes = []
        for blob in blobs:
            if blob.name.endswith('.parquet'):
                df = GoogleCloudStorage.with_config(ConfigFileLoader(config_path, config_profile)).load(
                    bucket_name,
                    blob.name,
                )
                dataframes.append(df)
        key = directory.split('/')[-1]  # Use the last part of the directory as the key
        all_data[key] = dataframes

    return all_data
