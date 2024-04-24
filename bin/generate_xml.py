# coding=utf-8
import pandas as pd
import numpy as np
import fnmatch #module for unix style pattern matching
import glob #module is used to retrieve files/pathnames matching a specified pattern
from datetime import datetime
from datetime import date
from yattag import Doc, indent
import argparse, hashlib, os, subprocess, sys, time

class Generate_xml:

    def __init__(self, action, dir):
        self.action = action
        self.dir = dir


    """
    Write pandas dataframe object to study xml file
    """
    def study_xml_generator(self, df, release_date=None):
        df = df.drop_duplicates(subset=['study_alias'])
        doc, tag, text = Doc().tagtext()
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>'
        #df = self.df#.loc[3: ,'study_alias':'release_date'] # trim the dataframe to the study section only
        #df = df.iloc[:, :-1]
        modified_df = df.where(pd.notnull(df), None) # replace the nan with none values
        doc.asis(xml_header)
        with tag('STUDY_SET'):
            for item in modified_df.to_dict('records'):
                if item['study_alias'] != None:
                    cleaned_item_dict = {k: v for k, v in item.items() if v not in [None, ' ']} # remove all the none and " " values
                    with tag('STUDY', alias=cleaned_item_dict['study_alias']):
                        with tag('DESCRIPTOR'):
                            with tag("STUDY_TITLE"):
                                text(cleaned_item_dict['study_name'])
                            doc.stag('STUDY_TYPE', existing_study_type="Other")
                            with tag('STUDY_ABSTRACT'):
                                text(cleaned_item_dict['abstract'])
                            with tag('CENTER_PROJECT_NAME'):
                                text(cleaned_item_dict['short_description'])
                        with tag('STUDY_ATTRIBUTES'):
                            for header, object in cleaned_item_dict.items():
                                if header not in ['study_alias', 'email_address', 'center_name', 'study_name',
                                                  'short_description', 'abstract']:
                                    with tag("STUDY_ATTRIBUTE"):
                                        with tag("TAG"):
                                            text(header)
                                        with tag("VALUE"):
                                            text(str(object))

        result_study = indent(
            doc.getvalue(),
            indent_text=False
        )

        if release_date is None:
            with open(f"{self.dir}/study.xml", "w") as f:
                f.write(result_study)
        else:
            with open(f"{self.dir}/study_{release_date}.xml", "w") as f:
                f.write(result_study)




    """
    Write pandas dataframe object to sample xml file
    """
    def sample_xml_generator(self, df):
        doc, tag, text = Doc().tagtext()
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>'
        #df = self.df#.loc[3:, 'sample_alias':'experiment_name'] # trim the dataframe to the sample section including the "experiment name" to include any user defined fields
        #df = df.iloc[:, :-1] # remove the last column in the trimmed dataframe ( the "experiment name" column)
        modified_df = df.where(pd.notnull(df), None) # replace the nan with none values
        doc.asis(xml_header)
        with tag('SAMPLE_SET'):
            for item in modified_df.to_dict('records'):
                if item['sample_alias'] != None:
                    cleaned_item_dict = {k: v for k, v in item.items() if v not in [None, ' ']} # remove all the none and " " values
                    if cleaned_item_dict:
                        with tag('SAMPLE', alias=cleaned_item_dict['sample_alias']):
                            with tag('TITLE'):
                                text(cleaned_item_dict['sample_title'])
                            with tag('SAMPLE_NAME'):
                                with tag("TAXON_ID"):
                                    text(cleaned_item_dict['tax_id'])
                                with tag("SCIENTIFIC_NAME"):
                                    text(cleaned_item_dict['scientific_name'])
                            with tag("DESCRIPTION"):
                                text(cleaned_item_dict['sample_description'])

                            with tag('SAMPLE_ATTRIBUTES'):
                                for header, object in cleaned_item_dict.items():
                                    if header not in ['sample_alias', 'sample_title', 'tax_id', 'scientific_name',
                                                      'sample_description']:
                                        with tag("SAMPLE_ATTRIBUTE"):
                                            with tag("TAG"):
                                                text(header)
                                            with tag("VALUE"):
                                                text(object)
                                            if header in ['geographic location (latitude)', 'geographic location (longitude)']:
                                                with tag("UNITS"):
                                                    text('DD')
                                            elif header in ['host age']:
                                                with tag("UNITS"):
                                                    text('years')



                                with tag("SAMPLE_ATTRIBUTE"):
                                    with tag("TAG"):
                                        text("ENA-CHECKLIST")
                                    with tag("VALUE"):
                                        text("ERC000033")

        result = indent(
            doc.getvalue(),
            indent_text=False
        )

        with open(f"{self.dir}/sample.xml", "w") as f:
            f.write(result)


    def submission_xml_generator(self, release_date=None):

        doc, tag, text = Doc().tagtext()
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>'
        doc.asis(xml_header)
        with tag('SUBMISSION_SET'):
            with tag('SUBMISSION'):
                with tag("ACTIONS"):
                    with tag('ACTION'):
                        doc.stag(self.action.upper())
                    if release_date is not None:
                        with tag('ACTION'):
                            doc.stag('HOLD', HoldUntilDate=str(release_date))

        result_s = indent(
            doc.getvalue(),
            indentation='    ',
            indent_text=False
        )
        if release_date is not None:
            with open(f"{self.dir}/submission_{str(release_date)}.xml", "w") as f:
                f.write(result_s)
            return f"{self.dir}/submission_{str(release_date)}.xml"
        else:
            with open(f"{self.dir}/submission.xml", "w") as f:
                f.write(result_s)
            return f"{self.dir}/submission.xml"
