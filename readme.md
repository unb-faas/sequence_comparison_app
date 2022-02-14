# Biological sequences comparison (Applications)
This project intends to perform biological sequences alignment using FASTA format in different cloud services such as on-demand instances (AWS EC2, Azure VM and GCP Cloud Compute) and function as a service (AWS Lambda, Azure Function, and Google Cloud Functions). 

## Alghorithm

- Hirschberg

## IaaS Applications
 - This project was developed on Python 3.6 and used these libraries:
    - General
        - base64 (request data manipulation)
        - fastapi (used for receive API requests on on-demand instances)
        - asyncio (used to perfom paralel processment on on-demand instances)
        - uvicorn
    - AWS
        - alignment (https://github.com/leebird/alignment)
        - boto3 (AWS S3 integration)
    - Azure
        - alignment (https://github.com/leebird/alignment)
        - azure-storage-blob (Blob Storage Integration)
        - python-dotenv
    - GCP
        - alignment (https://github.com/leebird/alignment)
        - google-cloud-storage (Cloud Storage integration)
    
## FaaS Functions
    - AWS
        - alignment (https://github.com/leebird/alignment)
        - boto3 (AWS S3 integration)
    - Azure
        - alignment (https://github.com/leebird/alignment) included directly into __init__.py
        - azure-storage-blob (Blob Storage Integration)
    - GCP
        - alignment (https://github.com/leebird/alignment)
        - google-cloud-storage (Cloud Storage integration)