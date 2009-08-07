if __name__ == '__main__':
    startOn = (nowutc() + timedelta(days = 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    Supervisor.getInstance().addTask(FoundationSyncTask(startOn=startOn))