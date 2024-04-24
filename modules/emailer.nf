#!/usr/bin/env nextflow

nextflow.enable.dsl=2 
//assigner_dir = "/scratch"
params.metadata_log = '/'
params.webinCli_log = '/'

process EMAILER {
	tag "emailer"                  
	label 'default'                
	//temp = "/temp"                
	//publishDir "/temp", mode: 'copy' 

input:
	path metadata_log
	path webinCli_log
	val sender_email
	val rec_email
	val password

output:
	stdout

    """
    Email sent successfully!
    """

script:
 """
	d_and_d_emailer.py --logdir_1 $metadata_log --logdir_2 $webinCli_log --sender_email $sender_email --rec_email $rec_email --password $password
 """
 }
 
 
workflow {
  EMAILER_CH = EMAILER(params.metadata_log, params.webinCli_log, params.sender_email, params.rec_email, params.password)
}
