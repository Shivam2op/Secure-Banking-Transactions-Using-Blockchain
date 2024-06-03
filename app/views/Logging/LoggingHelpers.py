import os

from django.urls import reverse

from bank.settings import BASE_DIR


def get_dir_files(path):
    filelist = []

    path = os.path.join(BASE_DIR, path)

    for file in os.listdir(path):
        if file.__str__().find('.log') > 0:
            filelist.append(file)

    return filelist


def get_system_files():

    filelist = get_dir_files('app/log/System')
    filelist.sort(reverse=True)

    links = []

    links += [
        ("Current Log File", reverse('app:SystemLogsDate', kwargs={
            'log_id': 1,
        }))
    ]

    for i in range(2, len(filelist)+1):
        file = 'app/log/System/'+filelist[i-2]
        links += [
            (file[file.rfind('.')+1:], reverse('app:SystemLogsDate', kwargs={
                'log_id': i,
            }))
        ]

    return links


def get_system_log(log_id):

    filelist = get_dir_files('app/log/System')
    filelist.sort(reverse=True)

    if int(log_id) > len(filelist):
        return None

    if int(log_id)==1:
        file = 'app/log/System/' + filelist[len(filelist)-1]
        file = os.path.join(BASE_DIR, file)
        return open(file, 'r').readlines()

    for i in range(2, len(filelist)+1):
        if int(i) == int(log_id):
            file = 'app/log/System/' + filelist[i-2]
            file = os.path.join(BASE_DIR, file)
            return open(file, 'r').readlines()


def get_transaction_files():

    filelist = get_dir_files('app/log/Transactions')
    filelist.sort(reverse=True)
    links = []
    links += [
        ("Current Transaction Log File", reverse('app:TransactionLogsDate', kwargs={
            'log_id': 1,
        }))
    ]

    for i in range(2, len(filelist)+1):
        file = 'app/log/Transactions/'+filelist[i-2]
        links += [
            (file[file.rfind('.')+1:], reverse('app:TransactionLogsDate', kwargs={
                'log_id': i,
            }))
        ]

    return links


def get_transaction_log(log_id):
    filelist = get_dir_files('app/log/Transactions')
    filelist.sort(reverse=True)

    if int(log_id) > len(filelist):
        return None

    if int(log_id)==1:
        file = 'app/log/Transactions/' + filelist[len(filelist)-1]
        file = os.path.join(BASE_DIR, file)
        return open(file, 'r').readlines()

    for i in range(2, len(filelist)+1):
        if int(i) == int(log_id):
            file = 'app/log/Transactions/' + filelist[i-2]
            file = os.path.join(BASE_DIR, file)
            return open(file, 'r').readlines()
