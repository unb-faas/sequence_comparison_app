# Biological sequences comparison (Applications)
This project intends to perform biological sequences alignment using FASTA format in different cloud services such as on-demand instances (AWS EC2) and function as a service (Lambda). 

## Alghorithm

- Hirschberg

## Application

This project was developed on Python 3.6 and used these libraries:
  - alignment (https://github.com/leebird/alignment)
  - boto3 (AWS S3 integration)
  - base64 (request data manipulation)
  - fastapi (used for receive API requests on on-demand instances)
  - asyncio (used to perfom paralel processment on on-demand instances)
