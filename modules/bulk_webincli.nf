#!/usr/bin/env nextflow

nextflow.enable.dsl=2 

process BULK_WEBINCLI {
	tag "bulk_webincli"                  
	label 'default'                

input:
	path spreadsheet
	val webin_account 
	val webin_password
    val context
    path files_dir
    val mode
    path webinCli_dir
	env environment

output:
	path "$files_dir/submissions/webin-cli.report", emit : webinCliend_report
	path "$files_dir/submissions", emit : webinCli_log

script:
if (params.environment.toLowerCase() == 'test') {
	"""
	bulk_webincli.py -s $spreadsheet -u $webin_account -p $webin_password -g $context -d $files_dir -m $mode -w $webinCli_dir -t
	"""
 }

  else if (params.environment.toLowerCase() == 'prod' || params.environment.toLowerCase() == 'production') {
	"""
	bulk_webincli.py -s $spreadsheet -u $webin_account -p $webin_password -g $context -d $files_dir -m $mode -w $webinCli_dir
	"""

 }

}
 
workflow {
   BULK_WEBINCLI = BULK_WEBINCLI(params.spreadsheet, params.webin_account, params.webin_password, params.context, params.files_dir, params.mode, params.webinCli_dir, params.environment)
}
