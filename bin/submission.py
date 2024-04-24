# coding=utf-8
# coding=utf-8
import pandas as pd
import numpy as np
import fnmatch #module for unix style pattern matching
import glob #module is used to retrieve files/pathnames matching a specified pattern
from yattag import Doc, indent
import argparse, hashlib, os, subprocess, sys, time


class Submission:
    def __init__(self, metadata, server, username, password, object_dir, submission_release_date=None, study_release_date=None):
        self.metadata = metadata
        self.server = server
        self.username = username
        self.password = password
        self.object_dir = object_dir
        self.submision_release_date= submission_release_date
        self.study_release_date = study_release_date

    """
    the submission command of the output xmls from the spreadsheet
    """
    def submission_command(self):
        if self.submision_release_date is None:
            submission_xml = f"{self.object_dir}/submission.xml"
        else:
            submission_xml= f"{self.object_dir}/submission_{self.submision_release_date}.xml"
        if self.study_release_date is None:
            study_xml = f"{self.object_dir}/{self.metadata.lower()}.xml"
        else:
            study_xml= f"{self.object_dir}/{self.metadata.lower()}_{self.submision_release_date}.xml"
        if self.server.lower() == 'test':
            baselink = "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/"
        elif self.server.lower() == 'prod':
            baselink = "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"
        else:
            print("please provide the submission server: test or prod")
            exit(1)
        command = 'curl -u {}:{} -F "SUBMISSION=@{}" -F "{}=@{}"  {}'.format(
            self.username, self.password,submission_xml ,self.metadata.upper(),study_xml, baselink)
        sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sp.communicate()
        print("-" * 100)
        print("CURL submission command: \n")
        print(command)
        print("Returned output: \n")
        print(out.decode())
        print("-" * 100)
        return out.decode()#, err.decode()