# About the Project
This nextflow pipeline automates the back end of the [SARS-CoV-2 Drag and Drop Uploader Tool](https://ebi-ait.github.io/sars-cov2-data-upload/), which was designed to make it easier to submit such raw and assembled sequence data to the European Nucleotide Archive (ENA).     
<br>
The Uploader Tool requires no technical skills from users and very little knowledge of the ENA’s submission process. It was developed in collaboration with the Archive Infrastructure and Technology (AIT) team and the ENA.

## About the pipeline/s
Once a user has uploaded their user metadata spreadsheet and data files via the front end of the tool (following the instructions [here](https://ebi-ait.github.io/sars-cov2-data-upload/app-documentation)), this nextflow pipeline should be run in order to:

1. Validate data file integrity
2. Validate metadata provided in the spreadsheet
3. Generate and submit (where necessary) Studies and Samples
4. Submit Runs and/or Analysis objects to the ENA via Webin-CLI
5. Send metadata and data submission receipts to a specified email address

**Please note there are 2 versions of this pipeline - the ‘main’ and the ‘stand-alone’**: 
<br>
- The ``main pipeline`` includes a file transfer and integrity check step, which moves files from an Amazon S3 bucket to the CODON cluster in the ENA, and verifies data file checksums.
- The ``stand-alone pipeline`` omits these steps.

# Getting started
## Installation
```
git clone https://github.com/ahmadazd/drag_and_drop_submission_workflow.git
```

### Install dependencies
(If you [run the pipeline using Docker or Singularity](ena_dragdrop_image), you can skip this step)
```
conda env create -f environment.yaml
```

# Running the pipeline
Regardless of which version of the pipeline you will be running, the ``nextflow.config`` file should first be edited like so in order to receieve the submission receipts:
```
params.sender_email= "<add sender email address here>"
params.rec_email= "<add receipient email address here>"
```

## Main pipeline
Run:
```
nextflow run pipeline/workflow/drag_and_drop_workflow/drag_and_drop_workflow.nf --webin_account su-<Webin-ID> --webin_password '<password>' --context <reads or genome> --mode <submit or validate> --senderEmail_password '<password>' --environment '<prod or test>'
```
specifying:
- The ``submitter’s Webin-ID``, with 'su' appended
- The ``ENA superuser password``
- The appropriate data context for Webin-CLI - i.e ``'reads' or 'genome'``
- The mode of submission - ``submit or validate``
- The ``password for the sender email account``
- The server to submit data to - ``'test' or 'production'``    

## Stand-alone pipeline
If you do not wish to transfer data and metadata files to the ENA compute cluster, and wish to skip the md5sum check, you can run the Stand-alone pipeline instead.
<br>
<br>
Make sure to first transfer all data files to the ```files``` directory, and the latest copy of the metadata spreadsheet to the ```spreadsheets``` directory.
<br>
<br>
Then run the pipeline as below:
```
nextflow run main.nf  --webin_account su-<Webin-ID> --webin_password '<password>' --context <reads or genome> --mode <submit or validate> --environment '<prod or test>'
```

## Output directories

- ```output/xml_archive``` : containing submitted Study and Sample xmls
- ```output/logs``` : log files for Study and Sample submission
- ```../webin-cli``` : output directory for Webin-CLI
- ```./transfer_output``` : **for main pipeline only**.  This will contain data files and the latest user spreadsheet uploaded via the tool, as well as md5 values and logs for the file transfer and integrity step of the pipeline.


## Running with Docker/Singularity
You can also run both versions of the pipelines in a Docker or Singularity container if you are concerned about operating system dependencies.    
Please make sure to install Docker or Singularity before using the images below.
<br>
For the ``main pipeline`` append your nextflow command with:
```
-with-docker enacontainers/ena_main_dragdrop_image
or
-with-singularity enacontainers/ena_main_dragdrop_image
```

For the ``Stand-alone pipeline`` append with:
```
-with-docker enacontainers/ena_dragdrop_image
or
-with-singularity enacontainers/ena_dragdrop_image
```
## Running with Conda
To run the pipeline with the Conda environment, append:
```
-profile conda
```
to either pipeline command.

## Contact
Ahmad Zyoud:     
Zahra Waheed: zahra@ebi.ac.uk
