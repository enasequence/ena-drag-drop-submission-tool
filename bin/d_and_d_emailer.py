#!/usr/bin/env python3
import smtplib # Simple Mail Transfer Protocol
import argparse
from argparse import RawTextHelpFormatter
import os
import fnmatch

description = """
This script emails 2 receipts to a specified recipient email address, 1. The Study + Sample metadata submission receipt and 2. The Webin-CLI data file submission receipt
"""

example = """
Example 1:
    python3 d_and_d_emailer.py -ld1 /mnt/c/Users/zahra/Desktop/covid_utils_tool_submissions/drag_and_drop_submission_workflow/metadata_out \n 
    -ld2 /mnt/c/Users/zahra/Desktop/covid_utils_tool_submissions/drag_and_drop_submission_workflow/webin_cli_out -s '###@ebi.ac.uk' -r '###@hotmail.co.uk' -p '###'
"""


parser = argparse.ArgumentParser(description=description, epilog=example, formatter_class=RawTextHelpFormatter)


parser.add_argument('-ld1', '--logdir_1', help='path to directory where all receipt XML log files are kept', type=str, required=True) # /mnt/c/Users/zahra/Documents/scripts/Python/drag_and_drop_submission_workflow/output/logs
parser.add_argument('-ld2', '--logdir_2', help='path to directory where Webin-CLI report log file is kept', type=str, required=True) # /mnt/c/Users/zahra/Documents/scripts/Python/drag_and_drop_submission_workflow/files/submissions
parser.add_argument('-s', '--sender_email', help='email address of sender', type=str, required=True) # password input is that of sender email
parser.add_argument('-p', '--password', help='password of the sender email', type=str, required=True) # password
parser.add_argument('-r', '--rec_email', help='email address of recipient', type=str, required=True) # email will be sent to here

args = parser.parse_args()



# read latest file, depending on logdir 1 or 2
# content is different according to 1 or 2

def setup_conn():
    setup_conn.smtp = smtplib.SMTP("outgoing.ebi.ac.uk", 587)  # according to email client
    setup_conn.smtp.starttls()  # TLS for security
    setup_conn.smtp.login(main.sender_email, main.password)
    print("Login success")

    # return smtp
    # subject = 'Drag and Drop Submission Status:'  # TODO: specify UUID in subject header?

def fetch_latest(logdir):
    wildcard = f"{logdir}"
    files = [f.path for f in os.scandir(wildcard)]  # os.scandir() faster than os.listdir(); but not suitable if dir has subdirs
    # print(files)
    latest_file = max(files, key=os.path.getctime)  # key to customise sort order, ctime = most recently changed file
    # print(latest_file)
    return latest_file


def send_email(file, header):

    with open(f'{file}', 'r') as tfile:  # latest metadata submission receipt
        body = tfile.read()
        print(tfile.read())

    content = header + '\n\n' + str(body)
    subject = 'Drag and Drop Submission Status:'  # TODO: specify UUID in subject header?
    mail_text = 'Subject:' + subject + '\n\n' + content  # to fix 'ascii' codec can't encode character '\xb5' in position 572: ordinal not in range(128) error
    print(mail_text)

    # mail_text = 'Subject:' + subject + '\n\n' + content  # to fix 'ascii' codec can't encode character '\xb5' in position 572: ordinal not in range(128) error
    # print(mail_text)

    # Send emails
    setup_conn.smtp.sendmail(main.sender_email, main.rec_email, mail_text.encode('utf-8'))
    print("email has been successfully sent to: ", main.rec_email)



def construct_email(logdir_1, logdir_2):

    if logdir_1 or logdir_2:

        if logdir_1 != 'null':
            latest_file_1 = fetch_latest(logdir_1)

            header_1 = \
                '-----------------------------------------' \
                '     Study/Sample submission receipt     ' \
                '-----------------------------------------'

            send_email(latest_file_1, header_1)


        if logdir_2 != 'null':
            latest_file_2 = fetch_latest(logdir_2)

            header_2 = \
                '-----------------------------------------' \
                '        Webin-CLI submission receipt     ' \
                '-----------------------------------------' 

            send_email(latest_file_2,header_2)


def main():

    # Argument variables
    main.sender_email = f'{args.sender_email}' # email being sent from
    main.rec_email = f'{args.rec_email}' # email being sent to
    main.password = args.password
    print("logdir one is ", args.logdir_1)
    print("logdir two is ", args.logdir_2)

    try:
        # Set up connection
        setup_conn()

        # Construct + send email for metadata receipt & Webin-CLI receipt
        construct_email(args.logdir_1,args.logdir_2)

    except Exception as e:
        print(f'\nERROR with sending emails: {e}\n')


if __name__ == '__main__':
    main()


