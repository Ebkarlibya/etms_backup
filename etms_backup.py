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
        "sites": ["site1.local", "pos2.erpbox.dev"],
        "type": "lxd",
        "container": "erp",
        "bench_path": "/home/ubuntu/frappe-bench",
        "backup_to": "/home/pop/Documents/lxd-backups",
        "validity_days": 2,
        "failure_mailto": "igentle.appletec@gmail.com",
    },
    {
        "sites": ["site2.local", "libyanstore.erpnext.ly"],
        "type": "lxd",
        "container": "erp",
        "bench_path": "/home/ubuntu/frappe-bench",
        "backup_to": "/home/pop/Documents/lxd-backups",
        "validity_days": 2,
        "failure_mailto": "igentle.appletec@gmail.com",
    }
]

def main():
    #handle tasks
    for task in BACKUP_TASKS:
        # Check old backups
        validity_days = task['validity_days']

        if task['validity_days'] > 0:
            backedup_files = os.listdir(task['backup_to'])

            for backup_name in backedup_files:
                d = backup_name.split("date:")
                if len(d) < 2:
                    continue
                backup_date = parse(d[1], fuzzy=True)

                if (datetime.datetime.now() - backup_date).days > validity_days:
                    backup_path = os.path.join(task['backup_to'], backup_name)
                    shutil.rmtree(backup_path)
                    print(f"ETMS Backup: Deleting invalid backup {backup_name}")
    
        if task['type'] == "lxd":
            # tmp working dir
            tmp_folder = tempfile.TemporaryDirectory()

            try:
                # backup each task site
                sites = task['sites']
                for site in sites:
                    subprocess.call(f"""
                        /snap/bin/lxc exec {task['container']} -- sudo --login --user ubuntu bash -ilc 
                        "cd frappe-bench && bench --site {site} backup --compress --with-files --backup-path /tmp/etms-backup"
                    """.replace("\n", ""),
                    shell=True)
                    # raise Exception("fobar")
                    # pull backup from lxd container
                    subprocess.check_call(
                        f"/snap/bin/lxc file pull -r {task['container']}/tmp/etms-backup {tmp_folder.name}",
                        shell=True)

                    # delete container /tmp/etms-backup folder
                    subprocess.check_call(f"""
                        /snap/bin/lxc exec {task['container']} -- sudo --login --user ubuntu bash -ilc "rm -rf /tmp/etms-backup"
                    """,
                    shell=True)
                    # format backup name
                    new_backup_name = f"{site}-date:{datetime.datetime.now().strftime('%Y-%m-%d:%H:%M')}"

                    src_path = os.path.join(tmp_folder.name, "etms-backup")
                    backup_to_path = os.path.join(task['backup_to'], new_backup_name)

                    shutil.move(src_path, backup_to_path)
            except Exception as e:
                print(e)
                notify_failure(task['failure_mailto'], site)


def notify_failure(failure_mailto, site):
    smtp_user = 'i.abdo@ebkar.ly'
    smtp_pass = 'ia@2008@IA'

    msg = EmailMessage()
    msg.set_content(f"""
        ETMS Backup System
        the backup proceess of your site: {site} faild
    """)

    msg['Subject'] = f"ETMS Backup, Site: {site} backup faild!"
    msg['From'] = smtp_user
    msg['To'] = failure_mailto

    try:
        smtp_server = smtplib.SMTP_SSL('mail.ebkar.ly', 465)
        # smtp_server.ehlo()
        smtp_server.login(smtp_user, smtp_pass)
        smtp_server.sendmail(smtp_user, failure_mailto, msg.as_string())
        smtp_server.close()
        print ("Email sent successfully!")
    except Exception as ex:
        print ("Something went wrong….",ex)


if __name__ == '__main__':
    main()