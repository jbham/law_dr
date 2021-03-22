#### NOTE: This project requires significant configuration. This project is not a plug and play software. However, once configuration is setup, the project works!

# Law Doctor

Law Doctor is an end to end multi-tenant application which allows Lawyers to upload patient's medical records and process them via CTAKES' NLP. In addition, it allows users to upload medical records as one large file with ALL medical records or single medical record. If a large file is submitted, then Law Doctor will split the document based on "Chief Complaints" or arbitrary word(s) specified in UI. 

Once the files are split and processed via CTAKES, Law Doctor attaches the medically relevant information, identified by CTAKES, back to the original document. This allows the end user to navigate the medically relevant information within the PDF in the browser.

Law Doctor also identifies the visit dates for each medical records and stores in data. Later, it present these dates as Timeline so the end user can navigate to different medical records from within the browsers. 


# High level Architecture diagram

 Application is designed to be hosted on AWS. See diagram below:
 
 ![Architecture Diagram](https://github.com/jbham/law_dr/blob/master/architecture_diagram.png)
 
 # Who would use this software?
 
 * If you are familiar with CTAKES, then this project would sure add value. 
 * Whoever deals with medical records, such as Lawyers, doctors, insurance companies, etc, and wants to extract medical information.
 * If you know Java, Python and Javascript along with different frameworks ReactJs and FastAPI. Also, it would help if you are familiar with AWS setup.

# AWS Tecnologies used:

* EC2
* Lambda
* RDS
* SQS
* Cognito
* S3
* VPC, Natgateway, security groups, etc
* Autoscaling

# How does this software works?

* Once all configuration is setup and application is fully up:
* An end user would be able to upload one or many medical records from the browser
  * App will communicate with API server -> get credentials and S3 upload path using STS for the specific user. Credentials are good for 15 minutes and will only work for user's IP address. This is accomplished using S3 bucket policy ```https://github.com/jbham/law_dr/blob/e7b263b08654b822a481bdc18c74b5d3f05a2fec/backend/app/app/crud/file.py#L144```.
  * App will show upload progress
  * As soon as the file is uploaded, app will communicate with 
    * REST API which communicates with RDS to track full progress of the file processing ```https://github.com/jbham/law_dr/blob/master/backend/app/app/crud/file.py```
    * Initiate lambda to start fetching files from S3 and start splitting them
      * This lambda ```https://github.com/jbham/law_dr/tree/master/backend/app/app/Lambda_functions/full_doc_splitter```:
        * updates RDS to track errors and progress of the file processing
        * pushes the split files back to S3 along with extracted text, which will be used by CTAKES processing, in separate txt files 
        * This lambda also pushes a message to SQS with payload related to what files to process
  * SQS initiates a lambda ```https://github.com/jbham/law_dr/tree/master/backend/app/app/Lambda_functions/job_manager``` which invokes the pipeline in CTAKES server (initially one; TODO: add auto scaling), depending on how many CORES are available for processing.
  * CTAKES server fetches S3 documents based on the information submitted in SQS payload. Payload specifies whether CTAKES' Default or Full pipeline needs to be processed.
  * Once CTAKES pipeline completes, it:
    * upload all terms back to S3 as JSON
    * intiates lambda to connect JSON details to the actual PDF document
    * updates RDS will status report (error, success, etc). If there is an error, then error is stores in DB for later review.
  * Lambda ```https://github.com/jbham/law_dr/blob/master/backend/app/app/Lambda_functions/mentions_extractor_refactored.py``` connects all terms/mentions of medically relevant information back to the original PDF document. This stitching of terms-to-pdf allows the user to navigate the complex information in an easy manner.
    * It identifies Visit Dates of each medical records
    * It updates RDS with full PDF coordinates along with CTAKES terms
    * updates RDS will status report (error, success, etc). If there is an error, then error is stores in DB for later review.

NOTE: 
* All S3 details, such as REGION, BUCKET, etc, Lambda name, SQS name are parameterized and are passed around via the payload submitted at different Stages. These parameterized values get passed to REST API (backend folder) via docker via environment values.
* If an error is encountered in any step above, then the error's full stacktrace is recorded in RDS.
* Two Lambdas, which are used for splitting documents and re-attaching CTAKES terms-to-pdf heavily uses PyMuPDF library with great performance.


Folder | Purpose
------------ | -------------
backend | REST API that works with frontend. Uses FASTAPI
ctakes | everything related to CTAKES. There are custom changes in this directory which are not part of original ctakes repo. Custom changes such document processing status, S3 file fetching and uploading, invoking lambda, etc
frontend | full blown ReactJS app that uses CoreUI React framework and AWS amplify.
backend/app/app/Lambda_functions/full_doc_splitter | Splits documents
backend/app/app/Lambda_functions/mentions_extractor_refactored.py | Attaches CTAKES term-to-pdf
backend/app/app/Lambda_functions/job_manager | Invokes CTAKES REST API to process document

# How database is setup?
This is accomplished in backend folder. Run below commands from ```backend/app/alembic```:

```
alembic revision --autogenerate -m "first push"
alembic upgrade head
```

# Is this the most optimal setup?
Of course not! This was the optimal setup for this project. Your mileage may vary. For instance, we could probably get rid of Natgateway to reduce cost and use some other AWS tech. However, for this use case, I did not get that far to bother.













 
