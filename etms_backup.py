#!/usr/bin/python3
import datetime
import os
import subprocess
import tempfile
import shutil
from dateutil.parser import parse
import smtplib
from email.message import EmailMessage



# Add Backup tasks below
BACKUP_TASKS = [
    {
        "sites": ["site1.local"],
        "type": "lxd",
        "container": "erp",
        # "src": "/home/ubuntu/frappe-bench/sites/site1.local/private/backups",
        "dst": "/home/pop/frappe-bench/bk_tmp",
        "old_backup_validity_days": 2,
        "failure_mailto": "igentle.appletec@gmail.com",
    }
]

def main():
    # etms_send_mail('i.abdo@ebkar.ly', 'igentle.appletec@gmail.com', 'ETMS Backup', 'etms notification')
    #handle tasks
    for task in BACKUP_TASKS:
        # Check old backups
        # old_backup_validity_days = task['old_backup_validity_days']

        # if task['old_backup_validity_days'] > 0:
        #     backedup_files = os.listdir(task['dst'])

        #     for backup_name in backedup_files:
        #         backup_date = parse(backup_name, fuzzy=True)

        #         if (datetime.datetime.now() - backup_date).days > old_backup_validity_days:
        #             backup_path = os.path.join(task['dst'], backup_name)
        #             shutil.rmtree(backup_path)
        #             print(f"Backup: {backup_name} exceeded the validity days ({old_backup_validity_days} Day) and got Deleted.")
    
        if task['type'] == "lxd":
            # tmp working dir
            tmp_folder = tempfile.TemporaryDirectory()

            try:
                # backup each task site
                sites = task['sites']
                for site in sites:
                    subprocess.call(f"""
                        lxc exec {task['container']} -- sudo --login --user ubuntu bash -ilc 
                        "cd frappe-bench && bench --site {site} backup --with-files --backup-path /tmp/etms-backup"
                    """.replace("\n", ""),
                    shell=True)

                    # pull backup from lxd container
                    subprocess.check_call(
                        f"lxc file pull -r {task['container']}/tmp/etms-backup {tmp_folder.name}",
                        shell=True)

                    # delete container /tmp/etms-backup folder
                    subprocess.check_call(f"""
                        lxc exec erp -- sudo --login --user ubuntu bash -ilc "rm -rf /tmp/etms-backup"
                    """,
                    shell=True)
                    # format backup name
                    new_backup_name = f"etms-backup:{site}-{datetime.datetime.now().strftime('%Y-%m-%d:%H:%M')}"

                    src_path = os.path.join(tmp_folder.name, "etms-backup")
                    dst_path = os.path.join(task['dst'], new_backup_name)

                    shutil.move(src_path, dst_path)
            except Exception as e:
                print(e)


def etms_send_mail(sender, receiver, subject, message):
    smtp_user = 'i.abdo@ebkar.ly'
    smtp_pass = 'ia@2008@IA'

    msg = EmailMessage()
    msg.set_content(message)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        smtp_server = smtplib.SMTP_SSL('mail.ebkar.ly', 465)
        # smtp_server.ehlo()
        smtp_server.login(smtp_user, smtp_pass)
        smtp_server.sendmail(sender, receiver, msg.as_string())
        smtp_server.close()
        print ("Email sent successfully!")
    except Exception as ex:
        print ("Something went wrong….",ex)


if __name__ == '__main__':
    main()