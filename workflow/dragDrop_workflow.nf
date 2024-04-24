// See the NOTICE file distributed with this work for additional information
// regarding copyright ownership.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Import modules/subworkflows
include { METADATA_SUBMISSION } from '../modules/metadata_submission.nf'
include { BULK_WEBINCLI } from '../modules/bulk_webincli.nf'
include { EMAILER as METADATA_EMAILER } from '../modules/emailer.nf' //to link the emailer.nf
include { EMAILER as WEBINCLI_EMAILER } from '../modules/emailer.nf' //to link the emailer.nf

workflow dragDrop_workflow {
conda = "${projectDir}/package-list.yaml" 
    take:
        spreadsheet
	    webin_account  
	    webin_password
        action
        xml_output
        context
        files_dir
        mode
        webinCli_dir
        sender_email
        rec_email
        password
        environment


    emit:
    metadata_emailer_ch
    bulkWebinCli_emailer_ch

    main:
        metadata_submission_ch = METADATA_SUBMISSION(spreadsheet, webin_account, webin_password, action, xml_output, environment)
        bulk_webincli_ch = BULK_WEBINCLI(METADATA_SUBMISSION.out.spreadsheet_log, webin_account, webin_password, context, files_dir, mode, webinCli_dir, environment)

        metadata_emailer_ch = METADATA_EMAILER(METADATA_SUBMISSION.out.metadata_log, '/' , sender_email, rec_email, password)
        bulkWebinCli_emailer_ch = WEBINCLI_EMAILER('/', BULK_WEBINCLI.out.webinCli_log, sender_email, rec_email, password)
}

workflow {
    dragDrop_workflow(params.spreadsheet, params.webin_account, params.webin_password, params.action, params.xml_output, params.context, params.files_dir, params.mode, params.webinCli_dir, params.sender_email, params.rec_email, params.password, params.environment)
}
