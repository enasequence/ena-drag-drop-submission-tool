# coding=utf-8
#!/usr/bin/env python3.7

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


class TrimmingSpreadsheet:
    def __init__(self, spreadsheet):
       self.spreadsheet = spreadsheet

    def __getitem__(self, index):
        return self.spreadsheet_parsed()[index], self.spreadsheet_upload()[index]


    """
    General trimming to the metadata in the spreadsheet and save it in a panda dataframe object
    """
    def trimming_the_spreadsheet(self, trimmed_df, metadata):
        trimmed_df["submission_tool"] = 'drag and drop uploader tool' #study #to inject constant into trimmed df


        if metadata == 'sample':
            trimmed_df["sample capture status"] = 'active surveillance in response to outbreak'
            trimmed_df.rename(columns={'collecting institute': 'collecting institution'},
                              inplace=True)  #####temp fix for collecting institute error
            trimmed_df.rename(columns={'collecting institute': 'collecting institution'}, inplace=True)
            trimmed_df["collection date"] = pd.to_datetime(trimmed_df["collection date"], errors='coerce').dt.strftime(
                "%Y-%m-%d")
            trimmed_df["receipt date"] = pd.to_datetime(trimmed_df["receipt date"], errors='coerce').dt.strftime("%Y-%m-%d")


        if metadata == 'study':
            trimmed_df["release_date"] = pd.to_datetime(trimmed_df["release_date"], errors='coerce').dt.strftime("%Y-%m-%d")

        return trimmed_df


    def spreadsheet_upload(self):
        if fnmatch.fnmatch(self.spreadsheet, '*.xls*'):
            latest_spreadsheet = self.spreadsheet
            metadata_df = pd.read_excel(latest_spreadsheet, header=0, sheet_name='Sheet1')
        elif fnmatch.fnmatch(self.spreadsheet, '*txt*') or fnmatch.fnmatch(self.spreadsheet, '*tsv*'):
            latest_spreadsheet = self.spreadsheet
            metadata_df = pd.read_csv(latest_spreadsheet, sep="\t", header=0, encoding= 'ISO-8859-1')
        elif fnmatch.fnmatch(self.spreadsheet, '*csv*'):
            latest_spreadsheet = self.spreadsheet
            metadata_df = pd.read_csv(latest_spreadsheet, sep=",", header=0, encoding= 'ISO-8859-1')
        else:
            wildcard = f"{self.spreadsheet}"
            all_files = [f.path for f in os.scandir(wildcard) if fnmatch.fnmatch(f, '*.xls*') or fnmatch.fnmatch(f, '*.txt*') or fnmatch.fnmatch(f, '*.tsv*') or fnmatch.fnmatch(f, '*.csv*')]
            latest_spreadsheet = max(all_files, key=os.path.getctime)
            if fnmatch.fnmatch(latest_spreadsheet, '*.xls*'):
                metadata_df = pd.read_excel(latest_spreadsheet, header=0, sheet_name='Sheet1')
            elif fnmatch.fnmatch(latest_spreadsheet, '*txt*') or fnmatch.fnmatch(latest_spreadsheet, '*tsv*'):
                metadata_df = pd.read_csv(latest_spreadsheet, sep="\t", header=0, encoding= 'ISO-8859-1')
            elif fnmatch.fnmatch(latest_spreadsheet, '*csv*'):
                metadata_df = pd.read_csv(latest_spreadsheet, sep=",", header=0, encoding= 'ISO-8859-1')
            else:
                print(f'you have used an unsupported spreadsheet: {latest_spreadsheet}, please try again')

        return [metadata_df, latest_spreadsheet]

    def spreadsheet_parsed(self):
        spreadsheet_df = self.spreadsheet_upload()
        study_df = spreadsheet_df[0].loc[:, 'Study':'Sample - Mandatory (ERC000033)']
        studyTrimmed_1_df = study_df.drop('Sample - Mandatory (ERC000033)', axis=1).drop([2, 1, 3], axis=0)
        studyTrimmed_2_df = studyTrimmed_1_df.rename(columns=studyTrimmed_1_df.iloc[0]).drop(
            studyTrimmed_1_df.index[0]).reset_index(drop=True)
        if pd.isnull(studyTrimmed_2_df['study_accession']).all():
            studyTrimmed_2_df = studyTrimmed_2_df.drop('study_accession', axis=1)
            StudyTrimmed_Final = self.trimming_the_spreadsheet(studyTrimmed_2_df, 'study')
        else:
            StudyTrimmed_Final = studyTrimmed_2_df

        try:
            analysis_df = spreadsheet_df[0].loc[:, 'Isolate Genome Assembly information':'Study']
            analysisTrimmed_df = analysis_df.drop('Study', axis=1).drop([2, 1, 3], axis=0)
            analysisTrimmedFinal = analysisTrimmed_df.rename(columns=analysisTrimmed_df.iloc[0]).drop(
                analysisTrimmed_df.index[0]).reset_index(drop=True)


            experiment_df = spreadsheet_df[0].loc[:, 'Run/Experiment information for associated raw reads':]
            experimentTrimmed_df = experiment_df.drop([2, 1, 3], axis=0)
            experimentTrimmedFinal = experimentTrimmed_df.rename(columns=experimentTrimmed_df.iloc[0]).drop(
                experimentTrimmed_df.index[0]).reset_index(drop=True)


            sample_df = spreadsheet_df[0].loc[:, 'Sample - Mandatory (ERC000033)':'Run/Experiment information for associated raw reads']
            sampleTrimmed_1_df = sample_df.drop('Run/Experiment information for associated raw reads', axis=1).drop([2, 1, 3], axis=0)
            sampleTrimmed_2_df = sampleTrimmed_1_df.rename(columns=sampleTrimmed_1_df.iloc[0]).drop(
                sampleTrimmed_1_df.index[0]).reset_index(drop=True)
            if pd.isnull(sampleTrimmed_2_df['sample_accession']).all():
                sampleTrimmed_2_df = sampleTrimmed_2_df.drop('sample_accession', axis=1)
                sampleTrimmed_Final = self.trimming_the_spreadsheet(sampleTrimmed_2_df, 'sample')
            else:
                sampleTrimmed_Final = sampleTrimmed_2_df

            return StudyTrimmed_Final, sampleTrimmed_Final, experimentTrimmedFinal, analysisTrimmedFinal

        except KeyError as e:
            if fnmatch.fnmatch(str(e), '*Isolate Genome Assembly information*'):
                experiment_df = spreadsheet_df[0].loc[:, 'Run/Experiment':]
                experimentTrimmed_df = experiment_df.drop([2, 1, 3], axis=0)
                experimentTrimmedFinal = experimentTrimmed_df.rename(columns=experimentTrimmed_df.iloc[0]).drop(
                    experimentTrimmed_df.index[0]).reset_index(drop=True)


                sample_df = spreadsheet_df[0].loc[:, 'Sample - Mandatory (ERC000033)':'Run/Experiment']
                sampleTrimmed_1_df = sample_df.drop('Run/Experiment', axis=1).drop([2, 1, 3], axis=0)
                sampleTrimmed_2_df = sampleTrimmed_1_df.rename(columns=sampleTrimmed_1_df.iloc[0]).drop(
                    sampleTrimmed_1_df.index[0]).reset_index(drop=True)
                if pd.isnull(sampleTrimmed_2_df['sample_accession']).all():
                    sampleTrimmed_2_df = sampleTrimmed_2_df.drop('sample_accession', axis=1)
                    sampleTrimmed_Final = self.trimming_the_spreadsheet(sampleTrimmed_2_df, 'sample')
                else:
                    sampleTrimmed_Final = sampleTrimmed_2_df

                return StudyTrimmed_Final, sampleTrimmed_Final, experimentTrimmedFinal

