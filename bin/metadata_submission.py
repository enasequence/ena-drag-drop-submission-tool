#!/usr/bin/env python3

# Copyright [2020] EMBL-European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import numpy as np
import fnmatch #module for unix style pattern matching
import glob #module is used to retrieve files/pathnames matching a specified pattern
from yattag import Doc, indent
import argparse, hashlib, os, subprocess, sys, time
from spreadsheet_parsing import TrimmingSpreadsheet
from generate_xml import Generate_xml
from submission import Submission
from bs4 import BeautifulSoup
import shutil
import datetime
from datetime import datetime
import lxml
import math

parser = argparse.ArgumentParser(prog='metadata-submission.py', formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
        + =================================================================================================================================== +
        |                           European Nucleotide Archive (ENA) Submission Tool                                                |
        |                                                                                                                                     |
        |  Tool to register study and sample metadata to an ENA project, mainly in the drag and drop tool context.                            |
        + =================================================================================================================================== +
        """)
parser.add_argument('-u', '--username', help='Webin submission account username (e.g. Webin-XXXXX)', type=str, required=True)
parser.add_argument('-p', '--password', help='password for Webin submission account', type=str, required=True)
parser.add_argument('-t', '--test', help='Specify whether to use ENA test server for submission', action='store_true')
parser.add_argument('-f', '--file', help='path for the metadata spreadsheet', type=str, required=True)
parser.add_argument('-a', '--action', help='Specify the type of action needed ( ADD or MODIFY)', type=str, required=True) # Modify flag is not working yet
parser.add_argument('-o', '--output', help='experimental spreadsheet output directory', type=str, required=True)
args = parser.parse_args()


def create_outdir(output):
    """
     create a directory
     :param output: the path for the output directory and the name of the directory to be created
     :returns the path and the name of the directory that been created
      """
    outdir = f"{output}"
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    return outdir


def study_sample_xml_generation(spreadsheet):
    """
     parse the ERC000033 spreadsheet
     :param spreadsheet: the path for the spreadsheet including the spreadsheet name
     :returns tuple with the study dataframe and sample dataframe
     """
    study_df = TrimmingSpreadsheet(spreadsheet).spreadsheet_parsed()[0]
    sample_df = TrimmingSpreadsheet(spreadsheet).spreadsheet_parsed()[1]

    return study_df, sample_df


def submission_command(metadata_type, release_date=None, study_release_date=None):
    """
    Navigate and calling the submission class for study and samples, moving the xmls into the archive directory after submission, create the log files
    :param metadata_type: study or sample
    :param release_date: in case of submission xml only, default : None
    :param study_release_date : in case of study only, default : None
    :returns the submission xml receipt
     """
    archive_dir = create_outdir(f'{args.output}/xml_archive') # create the archive folder
    log_dir = create_outdir(f'{args.output}/logs') # create the log folder
    print(log_dir)
    print(archive_dir)
    now = datetime.now()
    now_str = now.strftime("%d%m%y-%H%M") # datetime in minutes format
    if args.test is True:  # if there is a test flag
        submission_output = Submission(metadata_type, 'test', args.username, args.password,
                                       args.output, release_date, study_release_date).submission_command()  # submit using the test server

        ##Moving the submitted xml to an archive folder
        if release_date is not None:
            shutil.move(f'{args.output}/submission_{release_date}.xml', f'{archive_dir}/submission_{release_date}.xml')
        else:
            shutil.move(f'{args.output}/submission.xml', f'{archive_dir}/submission.xml')
        if study_release_date is not None:
            shutil.move(f'{args.output}/{metadata_type}_{release_date}.xml', f'{archive_dir}/{metadata_type}_{release_date}.xml')
        else:
            shutil.move(f'{args.output}/{metadata_type}.xml', f'{archive_dir}/{metadata_type}.xml')

        # Creating the log file
        with open(f'{log_dir}/submission_logs_{now_str}.txt', 'a') as f:
            f.write(submission_output)

        return submission_output

    if args.test is False:  # if there is no test flag
        submission_output = Submission(metadata_type, 'prod', args.username, args.password,
                                       args.output, release_date, study_release_date).submission_command()  # submit using the prod server

        ##Moving the submitted xml to an archive folder
        if release_date is not None:
            shutil.move(f'{args.output}/submission_{release_date}.xml', f'{archive_dir}/submission_{release_date}.xml')
        else:
            shutil.move(f'{args.output}/submission.xml', f'{archive_dir}/submission.xml')
        if study_release_date is not None:
            shutil.move(f'{args.output}/{metadata_type}_{release_date}.xml', f'{archive_dir}/{metadata_type}_{release_date}.xml')
        else:
            shutil.move(f'{args.output}/{metadata_type}.xml', f'{archive_dir}/{metadata_type}.xml')

        # Creating the log file
        with open(f'{log_dir}/submission_logs_{now_str}.txt', 'a') as f:
            f.write(submission_output)

        return submission_output  # return the submission output




def submission(metadata_type, study_df = None):
    """
        generate sample, study, submission xmls and calling the submission_command function for submission
        :param metadata_type: study or sample
        :param study_df: the study dataframe to be submitted, in case of study only, default : None
        :returns the submission xml receipt
         """

    if study_df is not None: #study submission
        study_df['release_date'] = pd.to_datetime(study_df['release_date'], format='%Y-%m-%d') #convert to timestamp
        release_date_list = [release_date for release_date in study_df['release_date'].dropna(axis=0).unique()] #collect the unique release_date

        if release_date_list: #if there a release date mention in the spreadsheet
            if len(release_date_list) > 1: #if there is more than one unique release date in the spreadsheet
                study_submission_xml_output = ''
                for index, row in study_df.dropna(subset=['study_alias'], axis=0).iterrows(): # collect each study to be submitted metadata row

                    row = row.to_frame().T # create a dataframe of each row
                    Generate_xml(args.action, args.output).study_xml_generator(row, row['release_date'].dt.strftime('%Y-%m-%d').str.cat(sep='\n'))  # generate the study xml for each study with unique release date
                    submission = Generate_xml(args.action, args.output).submission_xml_generator( row['release_date'].dt.strftime('%Y-%m-%d').str.cat(sep='\n'))  # generate the submission xml for each unique release date
                    submission_output = submission_command(metadata_type, row['release_date'].dt.strftime('%Y-%m-%d').str.cat(sep='\n'), row['release_date'].dt.strftime('%Y-%m-%d').str.cat(sep='\n'))  # pair and submit each study xml with its submission xml
                    study_submission_xml_output = f'{study_submission_xml_output}\n{submission_output}'  # collect all the output reciepts
                return study_submission_xml_output



            else: # in case there is only one unique release date
                print(str(release_date_list[0]))
                release_date_formatted = datetime.strptime(str(release_date_list[0]).rstrip("T00:00:00.000000000").strip(),'%Y-%m-%d').strftime('%Y-%m-%d')
                Generate_xml(args.action, args.output).study_xml_generator(study_df)  # generate the study xml for all the studies in a single xml
                submission = Generate_xml(args.action, args.output).submission_xml_generator(release_date_formatted)  # generate the submission xml for each unique release date
                submission_output = submission_command(metadata_type,release_date_formatted) #submit the study xml using the single release date
                return submission_output


        else: #in case there is no release date
            Generate_xml(args.action, args.output).study_xml_generator(
                study_df)  # generate the study xml for all the studies in a single xml
            submission = Generate_xml(args.action, args.output).submission_xml_generator() # generate study xml
            submission_output = submission_command(metadata_type) # submit and generate the submission xml without a hold date
            return submission_output

    else: #in case its not a study submission
        submission = Generate_xml(args.action, args.output).submission_xml_generator() # generate study xml
        submission_output = submission_command(metadata_type) #submit and generate the submission xml
        return submission_output




def experiment_analysis_spreadsheet():
    """
     parse the analysis/experiment metadata from the ERC000033 spreadsheet
     :returns experiment or analysis dataframe
    """
    try:
        analysis_df = TrimmingSpreadsheet(args.file).spreadsheet_parsed()[3].dropna(axis=0, how='all') # trim the analysis spreadsheet
        experiment_df = TrimmingSpreadsheet(args.file).spreadsheet_parsed()[2] #trim the experiment spreadsheet
        if not pd.isna(experiment_df['experiment_name']).all(): # if the experiment is not empty
            analysis_df = pd.concat([analysis_df, experiment_df], join = 'outer', axis = 1).dropna(axis=0, how='all')
        return analysis_df
    except IndexError: # no analysis section
        experiment_df = TrimmingSpreadsheet(args.file).spreadsheet_parsed()[2].dropna(axis=0, how='all') #trim the experiment spreadsheet
        return experiment_df


def main_spreadsheet():
    """
     upload and partially trim the ERC000033 spreadsheet
     :returns trimmed but fully intact spreadsheet as a dataframe
     """

    spreadsheet_original = TrimmingSpreadsheet(args.file).spreadsheet_upload()[0]
    spreadsheet_original = spreadsheet_original.drop(spreadsheet_original.columns[0], axis=1).drop([2, 1, 3], axis=0)
    spreadsheet_original = spreadsheet_original.rename(columns=spreadsheet_original.iloc[0]).drop(spreadsheet_original.index[0]).reset_index(drop=True)
    return spreadsheet_original


def fetching_receipt(receipt):
    """
     extract the xml receipt
     :returns xml receipt
      """
    xml_receipt = BeautifulSoup(receipt, features="lxml")
    return xml_receipt


def extract_accession_alias(xml_receipt, receipt_type):
    """
    extract the alias and the accession from xml receipt
    :param xml_receipt: xml receipt, the output of  from the fetching_receipt function
    :param receipt_type: sample or study
    :returns xml receipt
      """
    acc_list =[]
    alias_list = []

    for record in xml_receipt.findAll(receipt_type):
        acc_list.append(record.get('accession'))
        alias_list.append(record.get('alias'))

    return acc_list, alias_list



def study_acc_not_in_spreadsheet(spreadsheet_original, metadata, experiment_OR_analysis):
    """
    parse and navigate the study metadata that needs to be submitted
     :param spreadsheet_original: the full intact (partially trimmed) ERC000033 spreadsheet
     :param metadata: study and sample metadata dataframe
     :param experiment_OR_analysis: experiment_name or assemblyname, to flag if its analysis spreadsheet or experiment spreadsheet
     :returns the studies accession and alias lists as a dataframe after submission
     """
    study_submission = submission('study', metadata) # submit the study xml and return the output
    study_xml_receipt = fetching_receipt(study_submission)  # fetch the study xml reciept

    if study_xml_receipt.findAll(success="false"):  # if the submission failed
        print("Study Submission Has Failed")
        #exit(1)
        study_df_1 = metadata
        if 'study_accession' not in study_df_1:
            study_df_1['study_accession'] = None
        if experiment_OR_analysis:
            study_acc_df = study_df_1[['study_accession','study_alias']].merge(spreadsheet_original[['study_alias', 'sample_alias', experiment_OR_analysis]], on='study_alias', how='inner') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align studies positions relative to the samples and experiment/analysis without filling the NA's
        else:
            study_acc_df = study_df_1[['study_accession','study_alias']].merge(spreadsheet_original[['study_alias', 'sample_alias']], on='study_alias', how='inner') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align studies positions relative to the samples and experiment/analysis without filling the NA's
        return study_acc_df


    if experiment_OR_analysis == None: #there is no experiment or analyis needs to be submitted
        return study_submission


    else: #there is experiment or analysis needs to be submitted
        study_acc_alias = extract_accession_alias(study_xml_receipt, "study") #extract the accession and the alias from the reciept
        study_df_1 = pd.DataFrame({'study_accession': study_acc_alias[0], 'study_alias': study_acc_alias[1]},columns=['study_accession', 'study_alias'])
        study_acc_df = study_df_1.merge(spreadsheet_original[['study_alias', 'sample_alias', experiment_OR_analysis]], on='study_alias', how='inner') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align studies positions relative to the samples and experiment/analysis without filling the NA's
        return study_acc_df


def sample_acc_not_in_spreadsheet(spreadsheet_original, metadata, experiment_OR_analysis = None):
    """
        parse and navigate the sample metadata that needs to be submitted
         :param spreadsheet_original: the full intact (partially trimmed) ERC000033 spreadsheet
         :param experiment_OR_analysis: experiment_name or assemblyname, to flag if its analysis spreadsheet or experiment spreadsheet
         :returns the sample accession and alias lists as a dataframe after submission
         """

    sample_submission = submission('sample') #sample submission
    sample_xml_receipt = fetching_receipt(sample_submission)  # fetch the xml submission receipt
    if sample_xml_receipt.findAll(success="false"):  # if the submission failed
        print("Samples Submission have Failed")
        #exit(1)
        sample_df_1 = metadata
        if 'sample_accession' not in sample_df_1:
            sample_df_1['sample_accession'] = None
        if experiment_OR_analysis:
            sample_acc_df = sample_df_1[['sample_accession','sample_alias']].merge(spreadsheet_original[['study_alias', 'sample_alias', experiment_OR_analysis]], on='sample_alias', how='left').fillna(method='ffill') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align samples positions relative to the study and experiment/analysis and refill the NA's
        else:
            sample_acc_df = sample_df_1[['sample_accession','sample_alias']].merge(spreadsheet_original[['study_alias', 'sample_alias']], on='sample_alias', how='left').fillna(method='ffill') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align samples positions relative to the study and experiment/analysis and refill the NA's
        return sample_acc_df

    if experiment_OR_analysis == None: # there is no need to submit experiment or analysis, thus no need for experimental spreadsheet ( only samples needs to be submitted)
        return sample_submission

    else: # some or all the samples not needed to be submitted
        sample_acc_alias = extract_accession_alias(sample_xml_receipt, "sample") #extract the submitted samples accession and alias
        sample_df_1 = pd.DataFrame({'sample_accession': sample_acc_alias[0], 'sample_alias': sample_acc_alias[1]}, columns=['sample_accession', 'sample_alias'])

        sample_acc_df = sample_df_1.merge(spreadsheet_original[['study_alias', 'sample_alias', experiment_OR_analysis]], on='sample_alias', how='left').fillna(method='ffill') # merge the submitted accessions and alias with the reference spreadsheet ( original) to align samples positions relative to the study and experiment/analysis and refill the NA's
        return sample_acc_df


def samples_final_arrangment(spreadsheet_original,metadata, experiment_OR_analysis = None):
    """sample metadata arrangement section
       parse the sample dataframe and retrieve the parts that need to be submitted
       :param spreadsheet_original: the full intact (partially trimmed) ERC000033 spreadsheet
       :param metadata: study and sample metadata dataframe
       :param experiment_OR_analysis: experiment_name or assemblyname, to flag if its analysis spreadsheet or experiment spreadsheet
       :returns a full sample dataframe that contains new accession and the already submitted accessions
       """

    '''This Block in case there is no sample accession mentioned in all the spreadsheet, which means that all the aliases needs to be submitted'''
    if 'sample_accession' not in metadata[1]: # all sample metadata needs to be submitted
        sample_df = TrimmingSpreadsheet(metadata[1]).trimming_the_spreadsheet(metadata[1], 'sample')  # retrim the sample metadata
        sample_xml = Generate_xml(args.action, args.output).sample_xml_generator(sample_df)  # generate sample xml
        sample_acc_df = sample_acc_not_in_spreadsheet(spreadsheet_original,metadata[1], experiment_OR_analysis) #direct the metadata into submission
        return sample_acc_df


    else: #not all the samples metadata needs to be submitted
        '''This block in case there at least one study accession been mentioned'''
        '''filtering out the samples that needs to be submitted and the once are not'''
        samples_with_acc = []
        samples_without_acc = []
        for index, row in metadata[1].iterrows():
            if not pd.isna(row.iloc[0]):
                samples_with_acc.append(row.iloc[0]) # fetching the accession ready in the spreadsheet ( no need for submission)
            else:
                samples_without_acc.append(row.iloc[1]) # fetching the alias for the samples that missing accession ( need for submission)
        samples_without_acc_df= pd.DataFrame(samples_without_acc, columns=['sample_alias']) # dataframe for samples that needs accession



        '''Checking experimental/ analysis metadata'''

        if experiment_OR_analysis == None: # there is no need to submit experiment or analysis, thus no need for experimental spreadsheet ( only samples needs to be submitted)
            samples_without_acc_df = samples_without_acc_df.merge(metadata[1], on='sample_alias', how='inner').drop(
                'sample_accession', axis=1) # get the rest of the metadata for the samples that need submission
            sample_df = TrimmingSpreadsheet(samples_without_acc_df).trimming_the_spreadsheet(samples_without_acc_df,'sample') #retrim the sample metadata
            sample_xml = Generate_xml(args.action, args.output).sample_xml_generator(sample_df) #generate sample xml
            sample_acc_df = sample_acc_not_in_spreadsheet(spreadsheet_original, metadata[1]) # submit sample xml
            return sample_acc_df #return sample receipt


        else: # there is experiment/ analysis metadata to be submitted
            samples_with_acc_df = pd.DataFrame(samples_with_acc, columns=['sample_accession']) # collect sample accession that do not need to be submitted in dataframe
            samples_without_acc_df = samples_without_acc_df.dropna(axis=1)
            if samples_without_acc_df.empty: # in case there is no samples to be submitted
                sample_acc_df = samples_with_acc_df.merge(spreadsheet_original[['study_alias', 'sample_accession', 'sample_alias', experiment_OR_analysis]],
                                          on='sample_accession', how='left')#.fillna(method='ffill') # merge the sample accessions with the reference spreadsheet ( original) to align samples positions relative to the study and experiment/analysis and refill the NA's
            else: # in case there is samples to be submitted
                samples_with_acc_df = samples_with_acc_df.merge(
                    spreadsheet_original[['study_alias', 'sample_accession', 'sample_alias', experiment_OR_analysis]],
                    on='sample_accession', how='inner') # merge the samples accessions and alias with the reference spreadsheet ( original) to align samples positions relative to studies experiments/analysis
                samples_without_acc_df = samples_without_acc_df.merge(metadata[1], on ='sample_alias', how='inner').drop('sample_accession', axis=1) # get the rest of the metadata for the samples that need submission
                sample_df = TrimmingSpreadsheet(samples_without_acc_df).trimming_the_spreadsheet(samples_without_acc_df, 'sample') # retrim the sample metadata
                sample_xml = Generate_xml(args.action, args.output).sample_xml_generator(sample_df)# generate sample xml
                sample_acc_df = sample_acc_not_in_spreadsheet(spreadsheet_original,experiment_OR_analysis) # submit sample xml and collect and parse the submission receipt
                sample_acc_df = pd.concat([samples_with_acc_df,sample_acc_df], join='outer', axis=0).reset_index(drop=True) # rearrange all the samples together to be included in the experimental spreadsheet

    return sample_acc_df



def studies_final_arrangment(spreadsheet_original, metadata, experiment_OR_analysis = None):
    """study metadata arrangement section
       parse the study dataframe and retrieve the parts that need to be submitted
       :param spreadsheet_original: the full intact (partially trimmed) ERC000033 spreadsheet
       :param metadata: study and sample metadata dataframe
       :param experiment_OR_analysis: experiment_name or assemblyname, to flag if its analysis spreadsheet or experiment spreadsheet
       :returns a full study dataframe that contains new accession and the already submitted accessions
       """
    metadata_study = metadata[0].dropna(axis=0, how='all')

    '''This Block in case there is no study accession mentioned in all the spreadsheet, which means that all the aliases needs to be submitted'''
    if 'study_accession' not in metadata_study: # if all the studies needs to be submitted
        studies_to_be_submitted_df = metadata_study.drop_duplicates(subset=['study_alias'])
        study_acc_df = study_acc_not_in_spreadsheet(spreadsheet_original, studies_to_be_submitted_df, experiment_OR_analysis)# submit the study xml and fetch and parse the submission reciept
        if experiment_OR_analysis:
            study_acc_df = study_acc_df.merge(spreadsheet_original[['study_alias','sample_alias', experiment_OR_analysis]], on = ['study_alias','sample_alias', experiment_OR_analysis], how='right')
        else:
            study_acc_df = study_acc_df.merge(
                spreadsheet_original[['study_alias', 'sample_alias']],
                on=['study_alias', 'sample_alias'], how='right')


        '''This block in case there at least one study accession been mentioned'''

    else: #not all the studies needs to submitted
        if not pd.isna(metadata_study['study_accession']).any(): #if all the studies dont need submission
            study_acc_df = metadata_study['study_accession'].to_frame(name='study_accession') #collect the accession in a dataframe


        else: #if some of the studies needs to be submitted
            studies_to_be_submitted = []
            alias_to_be_submitted = []
            studies_without_submission_list = []
            study_alias_list = []
            for index, value in metadata_study.iterrows(): #divide the studies accessions and alias to separate dataframes as needs to be submitted and dont
                if value[1] not in study_alias_list:
                    study_alias_list.append(value[1])
                    if pd.isna(value[0]):
                        studies_to_be_submitted.append(value)
                        alias_to_be_submitted.append(value[1])
                    else:
                        studies_without_submission_list.append(value)

            studies_without_submission_df = pd.DataFrame(studies_without_submission_list,columns=['study_accession', 'study_alias']).reset_index(drop=True) # collect the accessions and alias of the studies that dont need submission
            studies_to_be_submitted_df = pd.DataFrame(alias_to_be_submitted,columns=['study_alias']) #collect the accession column and alias for the studies that needs submission
            studies_to_be_submitted_df = studies_to_be_submitted_df.merge(metadata_study, on='study_alias', how='inner') #merge the studies with the rest of the column to align and fetch the rest of the study metadata


            '''Checking experimental/ analysis metadata'''

            if experiment_OR_analysis == None: # if the experiment and the analysis not needed to be submitted
                study_df = TrimmingSpreadsheet(studies_to_be_submitted_df).trimming_the_spreadsheet(studies_to_be_submitted_df,'study') #retrim the study metadata
                study_submission = submission('study', study_df) # submit the study xml
                return study_submission # return the submission output


            else: #if there experiment or analysis needs to be submitted
                studies_without_submission_df = pd.merge(studies_without_submission_df, spreadsheet_original[
                    ['study_accession', 'study_alias', 'sample_alias', experiment_OR_analysis]],
                                                         on=['study_accession', 'study_alias'],
                                                         how='outer') #merge the studies accessions and alias with the reference spreadsheet ( original) to align studies positions relative to studies experiments/analysis
                studies_without_submission_df = pd.DataFrame(
                    [value for index, value in studies_without_submission_df.iterrows() if
                     value[1] not in alias_to_be_submitted],
                    columns=['study_accession', 'study_alias', 'sample_alias', experiment_OR_analysis]).sort_values(
                    by=['study_alias']) # align and loop into the studies that needs to be submitted to make sure all are captured

                studies_without_submission_df[['study_accession']] = studies_without_submission_df[
                    ['study_accession']].fillna(method='ffill') #Fill the NA's


                '''Final check if there is no Studies need to be submitted'''
                if not studies_to_be_submitted_df.empty:
                    study_df = TrimmingSpreadsheet(studies_to_be_submitted_df).trimming_the_spreadsheet(
                        studies_to_be_submitted_df,'study') #trim the studies to be submitted metadata into the standards
                    study_acc_df = study_acc_not_in_spreadsheet(spreadsheet_original, study_df, experiment_OR_analysis) #submit and fetch the submission xml reciept
                    study_acc_df = pd.concat([study_acc_df, studies_without_submission_df], join='outer', axis=0).reset_index(drop=True) ## collect the accessions and alias of the studies that dont need submission
                else:
                    study_acc_df = studies_without_submission_df

    return study_acc_df

def chromosome_list(value):
    new_value = f'{value.strip("*.fasta.gz")}_chromosomelist.txt.gz'
    return new_value


def create_new_spreadsheet_with_Accession(spreadsheet_original,metadata_acc, experiment_OR_analysis ):
    spreadsheet_original_modified = spreadsheet_original.drop(['study_accession', 'sample_accession'], axis=1)
    updated_original_spreadsheet = pd.merge(spreadsheet_original_modified, metadata_acc,
                                            on=[experiment_OR_analysis, "study_alias", "sample_alias"],
                                            how='left')  # concat the study+sample metadata with the original spreadsheet
    original_columns = list(spreadsheet_original.columns)
    updated_original_spreadsheet = updated_original_spreadsheet.reindex(columns=original_columns)
    spreadsheet_NoTrimming = TrimmingSpreadsheet(args.file).spreadsheet_upload()[0]
    latest_spreadsheet_path = TrimmingSpreadsheet(args.file).spreadsheet_upload()[1]
    spreadsheet_NoTrimming_columns = list(spreadsheet_NoTrimming.columns)
    top_columns = spreadsheet_NoTrimming.iloc[0:4]
    first_column = spreadsheet_NoTrimming['Unnamed: 0'].drop([2, 1, 3], axis=0)
    updated_original_spreadsheet.insert(0, 'Unnamed: 0', first_column)
    updated_original_spreadsheet.columns = spreadsheet_NoTrimming_columns
    updated_original_spreadsheet = pd.concat([top_columns, updated_original_spreadsheet]).reset_index(drop=True)
    updated_original_spreadsheet.to_excel(
        f"{latest_spreadsheet_path.rstrip('withAccessions.xlsx').rstrip('xls').rstrip('xlsx').rstrip('txt').rstrip('csv')}.withAccessions.xlsx",
        index=False)  # print out the the modified spreadsheet




def main():

    """The main section"""

    spreadsheet_original = main_spreadsheet()  # capture the spreadsheet for reference
    create_outdir(args.output) # create the output directory
    create_outdir(f'{args.output}/logs')  # create the log folder

    for submission_logs in glob.glob(f'{args.output}/logs/submission_logs_*'):
        if os.path.exists(submission_logs):
            create_outdir(f'{args.output}/logs/archived_logs')
            shutil.move(submission_logs, f'{args.output}/logs/archived_logs/{os.path.basename(submission_logs)}')

    '''
    This block will run only if there is an experimental/analysis part filled in the spreadsheet
    '''
    if not pd.isna(spreadsheet_original['experiment_name']).all() or 'assemblyname' in spreadsheet_original:  # at least the experiment (runs) or the analysis (assemblies) metadata needs for submission
        if not pd.isna(spreadsheet_original['experiment_name']).all():  # contains experiment (runs) metadata
            experiment_OR_analysis = 'experiment_name'  # reference for experiment data
        else:  # contains analysis data only
            experiment_OR_analysis = 'assemblyname'  # reference for analysis data
        metadata = study_sample_xml_generation(args.file)  # fetch the study and samples metadata separately using uploaded again
        metadata_study = metadata[0].dropna(axis=0, how='all')
        experimental_spreadsheet = experiment_analysis_spreadsheet()  # fetch the experiment and the analysis metadata

        '''
        This for Sample submission which will produce a data frame with sample_accession, sample_alias, related study_alias and experimntal/analysis names
        '''

        sample_acc_df = samples_final_arrangment(spreadsheet_original, metadata, experiment_OR_analysis)  # parse and submit the sample metadata if needed.


        '''
        This block for study submissions if exist or accession arrangment which will submit the studies if needed and merge the the study metadata with the sample metadata the been produced from the block above
        '''

        if 'study_accession' not in metadata_study:  # all studies needs to be submitted
            study_acc_df = studies_final_arrangment(spreadsheet_original, metadata,
                                                    experiment_OR_analysis)  # arrange the studies format
            metadata_acc = study_acc_df.merge(sample_acc_df, on=['study_alias', 'sample_alias', experiment_OR_analysis], how='outer').drop_duplicates(
                keep='first').dropna(how='all').fillna(method='ffill')  # merge the study dataframe with the sample dataframe after all the metadata that needs to be submitted is processed



        else:  # some studies needs to be submitted
            if not pd.isna(metadata_study['study_accession']).any():  # all the studies dont need any submission
                study_acc_df = studies_final_arrangment(spreadsheet_original, metadata, experiment_OR_analysis)  # arrange the studies metadata format
                metadata_acc = pd.concat([study_acc_df, sample_acc_df], join='outer', axis=1).ffill()  # merge the study dataframe with the sample dataframe after all the metadata that needs to be submitted is processed and fill the NA's


            else:  # some studies needs to be submitted and some are not
                study_acc_df = studies_final_arrangment(spreadsheet_original, metadata,
                                                        experiment_OR_analysis)  # arrange the studies metadata format
                metadata_acc = study_acc_df.merge(sample_acc_df,
                                                  on=['study_alias', 'sample_alias', experiment_OR_analysis],
                                                  how='outer').drop_duplicates(keep='first') # merge the study dataframe with the sample dataframe after all the metadata that needs to be submitted is processed and remove duplicates



        '''
        This block to create the full output spreadsheet (the experimental spreadsheet) that results from merging the output from the previous block (sample and study metadata) with experiment/analysis metadata
        '''

        experimental_spreadsheet = metadata_acc.merge(experimental_spreadsheet, on=experiment_OR_analysis,how='right')  # concat the study+sample metadata with the experiment/analysis metadata

        create_new_spreadsheet_with_Accession(spreadsheet_original, metadata_acc,experiment_OR_analysis)


        experimental_spreadsheet = experimental_spreadsheet.drop(['study_alias', 'sample_alias'], axis=1)  # remove the aliases
        if os.path.exists(f"{args.output}/experimental_spreadsheet.xlsx"):
            os.remove(f"{args.output}/experimental_spreadsheet.xlsx")


        if not pd.isna(experimental_spreadsheet['study_accession']).any() and not pd.isna(experimental_spreadsheet['sample_accession']).any():
            experimental_spreadsheet = experimental_spreadsheet.dropna(axis=1, how='all')  # remove the empty columns
            experimental_spreadsheet["submission_tool"] = 'drag and drop uploader tool'  # to inject submission_tool into experimental_spreadsheet
            if experiment_OR_analysis == 'assemblyname':
                experimental_spreadsheet["chromosome_list"] = experimental_spreadsheet["fasta/flatfile name"].apply(chromosome_list)

            experimental_spreadsheet.to_excel(f"{args.output}/experimental_spreadsheet.xlsx",
                                              index=False)  # print out the experiment spreadsheet



        '''
        This block will run only if there is NO an experimental/analysis part filled in the spreadsheet
        '''
    else:  # if experiment and analysis are not needed to be submitted
        metadata = study_sample_xml_generation(
            args.file)  # fetch the study and samples metadata separately using uploaded again
        study_submission = studies_final_arrangment(spreadsheet_original, metadata)  # arrange the study metadata format and generate the xml and submit, return the submission output
        sample_submission = samples_final_arrangment(spreadsheet_original, metadata)  # arrange the sample metadata format and generate the xml and submit, return the submission output



if __name__ == '__main__':
    main()



