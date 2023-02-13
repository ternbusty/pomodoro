from time import sleep
from utils import Utils
from datetime import datetime
from datetime import timedelta
import threading


class Timer:
    def __init__(self) -> None:
        self.reset()
        self.utils = Utils()

    def reset(self) -> None:
        self.status: str = "not_started"
        self.can_take_long_break: bool = True
        self.task_name: str = None
        self.work_timer: int = 1500
        # self.break_timer: int = 5
        self.break_timer: int = 300
        self.total_working_timer: int = 0
        self.is_lazy: bool = False
        self.histories: list = []
        self.summary_text: str = ""

    def get_status(self) -> dict:
        status = {
            "status": self.status,
            "task_name": self.task_name,
            "timers": {
                "work_timer": self.work_timer,
                "break_timer": self.break_timer,
                "total_working_timer": self.total_working_timer}}
        return status

    def get_history(self) -> str:
        history_text = content = ""
        for history in self.histories:
            if history[0] == "start_break":
                content = "Take a break"
            else:
                content = f"Start {history[2]}"
            datetime_text = self.utils.format_date(history[1])
            history_text += f"{datetime_text}\t{content}\n"
        return history_text

    def start_work(self, task_name: str = "working") -> None:
        if self.break_timer < 0:
            self.work_timer += -1 * self.break_timer
            self.break_timer = 0
        self.status = "work"
        self.task_name = task_name
        row = ["start_work", datetime.now(), task_name]
        print(row)
        self.histories.append(row)

    def start_break(self, break_time: int = 0) -> None:
        self.status = "break"
        self.break_timer += break_time
        row = ["start_break", datetime.now(), "Break"]
        print(row)
        self.histories.append(row)

    def take_long_break(self, break_time: int = 0) -> None:
        if not self.can_take_long_break:
            return
        self.start_break(break_time)
        self.can_take_long_break = False
        # self.long_break_cnt = 1800
        # while
        sleep(1800)
        self.can_take_long_break = True

    def terminate(self) -> str:
        self.reset()

    def summarize(self) -> str:
        self.histories.append(["end", datetime.now(), "End today's job"])
        print(self.histories)
        current_task_name: str = None
        task_start_dt: datetime = None
        break_start_dt: datetime = None
        current_break_timedelta = total_break_timedelta = timedelta(0)
        current_task_timedelta = total_work_timedelta = timedelta(0)

        for history in self.histories:
            dt = history[1]
            content = history[2]
            if history[0] == "start_break":
                # If break is not in progress, update break_star_timestamp with a new one
                if break_start_dt is None:
                    break_start_dt = dt
            else:
                # If break is in progress, end break
                if break_start_dt is not None:
                    tmp_break_timedelta: timedelta = dt - break_start_dt
                    current_break_timedelta += tmp_break_timedelta
                    total_break_timedelta += tmp_break_timedelta
                    break_start_dt = None
                # Check if the work is a new one
                if content == current_task_name:
                    continue
                # End the current task if exists
                if current_task_name is not None:
                    current_task_timedelta = dt - task_start_dt - current_break_timedelta
                    current_task_timedelta_str = self.utils.convert_timedelta_to_str(
                        current_task_timedelta)
                    current_break_timedelta_str = self.utils.convert_timedelta_to_str(
                        current_break_timedelta)
                    self.summary_text += f"{self.utils.format_date(task_start_dt)}\t{current_task_name}\t{current_task_timedelta_str}\t{current_break_timedelta_str}\n"
                # Start new task
                current_task_name = content
                task_start_dt = dt
                current_break_timedelta = timedelta(0)

        total_break_str = self.utils.convert_timedelta_to_str(total_break_timedelta)
        total_work_str = self.utils.convert_timedelta_to_str(total_work_timedelta)
        self.summary_text += f"{self.utils.format_date(dt)}\tTotal\t{total_work_str}\t{total_break_str}"
        print(self.summary_text)
        self.status = "finished"
        self.utils.send_to_discord(self.summary_text)
        return self.summary_text

    def main(self, break_time) -> None:
        self.reset()
        self.histories.append(["start_work", datetime.now(), "Opening"])
        self.start_break(break_time)
        while True:
            print(self.work_timer, self.break_timer, self.total_working_timer)
            if self.status == "work":
                self.work_timer -= 1
                self.total_working_timer += 1
            elif self.status == "break":
                self.break_timer -= 1
                if self.break_timer <= 0:
                    self.is_lazy = True
                    if self.break_timer % 90 == 0:
                        try:
                            thread = threading.Thread(target=self.utils.call_me, name="callMe")
                            thread.start()
                        except BaseException:
                            print("Failed to call me")
            else:
                break
            sleep(1)
