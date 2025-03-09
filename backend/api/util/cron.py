from crontab import CronTab


def create_cron_job(command: str, schedule: str, id: str) -> bool:
    try:
        cron = CronTab(user=True)
        job = cron.new(command=command, comment=id)
        job.setall(schedule)
        cron.write()
        return True
    except:
        return False


def kill_cron_job(id: str) -> bool:
    try:
        cron = CronTab(user=True)
        for job in cron:
            if job.comment == id:
                cron.remove(job)
                cron.write()
                break
        return True
    except:
        return False


def update_cron_job(command: str, schedule: str, id: str) -> bool:
    try:
        cron = CronTab(user=True)
        for job in cron:
            if job.comment == id:
                job.set_command(command)
                job.setall(schedule)
                cron.write()
                break
        return True
    except:
        return False


def main():
    # create_cron_job('echo hello_world', '228')
    # kill_cron_job('228') # убийство крон джобы не работает, посмотреть!!!
    # create_cron_job('echo hello_world', '* * * * *', '228')
    update_cron_job('echo hello_world', '*/10 * * * *', '228')


if __name__ == '__main__':
    main()
