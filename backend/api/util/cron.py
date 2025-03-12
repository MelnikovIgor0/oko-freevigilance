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
