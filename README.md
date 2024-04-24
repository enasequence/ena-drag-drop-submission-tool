# drag_and_drop_submission_workflow
metadata_submission command to run standalone  
` python3 metadata_submission.py -f <spreadsheet_dir> -u <Webin-####> -p <'password'> -a add -t -o <output_dir>`

bulk_webincli command to run standalone
` python3 bulk_webincli.py -s <spreadsheet_dir> -d <files_dir> -m <mode(submit/validate)> -u <Webin-####> -p <'password'> -g <context> -w <webin_cli software directory>`

nextflow "standalone" pipeline command to run
`nextflow run main.nf  --webin_account <Webin-####> --webin_password <'password'> --context <context(reads/genome..etc)> --mode <mode(submit/validate)> --environment <test/prod>`

To use the pipeline conda environment, add the parameter : `-profile conda` 

to use the docker/singularity container, add the parameter : `with-docker [docker image]` or `-with-singularity [singularity/docker image file]`

Image name : `enacontainers/ena_dragdrop_image`

### NOTE: please make sure to install docker or singularity before using the image.

files directory: contains the files to be submitted (contains files for testing)

output directory : contains the metadata_submission outputs ((experimental_spreadsheet)) and log files

webin-cli directory : contains the webin_cli software

spreadsheets directory : contains the metadata spreadsheet (contains two template spreadsheets)

### NOTE: before running the Nextflow workflow run the following commands:

`mkdir files spreadsheets` (to create two empty directories, files and spreadsheets. Please then move data files and the metadata spreadsheet to the appropriate directory)

