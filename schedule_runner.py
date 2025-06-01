from apscheduler.schedulers.blocking import BlockingScheduler
import lotto_updater
import datetime

def scheduled_job():
    print(f"[{datetime.datetime.now()}] 자동 업데이트 실행")
    lotto_updater.update_latest_lotto()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # 매주 토요일 밤 9시 (로또 발표 이후)
    scheduler.add_job(scheduled_job, 'cron', day_of_week='sat', hour=21, minute=0)
    print("🔁 로또 자동 업데이트 스케줄러 시작됨")
    scheduler.start()
