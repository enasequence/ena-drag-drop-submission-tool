#!/usr/bin/env nextflow

nextflow.enable.dsl=2 

params.transfer_output = "/"
params.transfer_flag = "/"

process TRANSFER_INTEGRITY {
	tag "transfer_integrity"                  
	label 'default'                
	//publishDir "$log_dir", mode: 'copy' 

input:
	val uuid
	path transfer_output // optional input value? user specified output dir
	val transfer_flag // for script flags without value input


output:
	path "$transfer_output/transfer_integrity_output/input_spreadsheet", emit: spreadsheet_dir, optional: true // path to user metadata spreadsheet
	path "$transfer_output/transfer_integrity_output/pass", emit: dataFiles_dir, optional: true // path to pass data files folder



script:

if (params.transfer_output != "/") {
	if (params.transfer_flag == 's') {
	"""
	echo transferring spreadsheets only
	echo to user specified output directory

	transfer_integrity_check.py -u $uuid -s -o $PWD/$transfer_output
	"""
	}
	
	else if (params.transfer_flag == 'd') {
	"""
	echo transferring data files only
	echo to user specified output directory

	transfer_integrity_check.py -u $uuid -d -o $PWD/$transfer_output
	"""
	}
	else if (params.transfer_flag == "/") {
	"""
	echo transferring all data to default directory

	transfer_integrity_check.py -u $uuid -o $PWD/$transfer_output 
	"""
	}
}
else if (params.transfer_output = "/") {
	if (params.transfer_flag == 's') {
	"""
	echo transferring spreadsheets only
	echo to default codon location
	
	transfer_integrity_check.py -u $uuid -s
	"""
	}
	
	else if (params.transfer_flag == 'd') {
	"""
	echo transferring data files only
	echo to default codon location
	
	transfer_integrity_check.py -u $uuid -d
	"""
	}
	else if (params.transfer_flag == "/") {
        """
        echo transferring all data to default directory

        transfer_integrity_check.py -u $uuid
        """
	}	
}
}

workflow {
   TRANSFER_INTEGRITY_CH = TRANSFER_INTEGRITY(params.uuid, params.transfer_output, params.transfer_flag) 
}
