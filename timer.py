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
        self.prev_status: str = None
        self.can_take_long_break: bool = True
        self.task_name: str = None
        self.work_timer: int = 1500
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
                content = history[2]
            else:
                content = f"Start {history[2]}"
            datetime_text = self.utils.format_date(history[1])
            history_text += f"{datetime_text}\t{content}\n"
        return history_text

    def start_work(self, task_name: str = "working") -> None:
        if self.status in ["not_started", "finished"]:
            return
        if self.break_timer < 0:
            self.work_timer += -1 * self.break_timer
            self.break_timer = 0
        self.status = "work"
        self.task_name = task_name
        row = ["start_work", datetime.now(), task_name]
        print(row)
        self.histories.append(row)

    def start_break(self, break_time: int = 0) -> None:
        if self.status in ["not_started", "finished"]:
            return
        if break_time >= 1800:
            if not self.can_take_long_break:
                return
        self.status = "break"
        self.break_timer += break_time
        row = ["start_break", datetime.now(), "Take a break"]
        print(row)
        self.histories.append(row)
        if break_time >= 1800:
            self.take_long_break()

    def take_long_break(self) -> None:
        self.can_take_long_break = False
        sleep(21600)
        self.can_take_long_break = True

    def terminate(self) -> None:
        self.reset()

    def pause(self) -> None:
        if self.status not in ["work", "break"]:
            return
        self.prev_status = self.status
        self.status = "pause"
        self.histories.append(["start_break", datetime.now(), "Start pause"])

    def summarize(self) -> str:
        if self.status in ["not_started", "finished"]:
            return
        self.histories.append(["end", datetime.now(), "End today's job"])
        print(self.histories)
        current_task_name: str = None
        task_start_dt: datetime = None
        break_start_dt: datetime = None
        pause_start_dt: datetime = None
        pause_str: str = ""
        current_break_timedelta = total_break_timedelta = timedelta(0)
        current_task_timedelta = total_work_timedelta = timedelta(0)

        for history in self.histories:
            dt = history[1]
            content = history[2]
            if pause_start_dt is not None:
                pause_str += f"-{self.utils.format_time(dt)} "
                pause_start_dt = None
            if history[0] == "start_break":
                # If break is not in progress, update break_start timestamp with a new one
                if break_start_dt is None:
                    break_start_dt = dt
                if content == "Start pause":
                    if pause_start_dt is None:
                        pause_start_dt = dt
                        pause_str += self.utils.format_time(dt)
            else:  # history[0] == "start_work"
                content = self.utils.add_quotation(content)
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
                total_work_timedelta += current_task_timedelta
                current_break_timedelta = timedelta(0)

        total_break_str = self.utils.convert_timedelta_to_str(total_break_timedelta)
        total_work_str = self.utils.convert_timedelta_to_str(total_work_timedelta)
        self.summary_text += f"{self.utils.format_date(dt)}\tTotal\t{total_work_str}\t{total_break_str}"
        summary_text_discord = self.summary_text
        if len(pause_str) != 0:
            summary_text_discord += f"\nPause: {pause_str}\n"
        print(self.summary_text)
        self.status = "finished"
        self.utils.send_to_discord(summary_text_discord)
        return self.summary_text

    def main(self, break_time) -> None:
        # If the current status is "work" or "break", ignore the start signal
        if self.status in ["work", "break"]:
            return
        # If the current status is "pause", restore the status
        if self.status == "pause":
            if self.prev_status == "work":
                self.start_work(self.task_name)
            elif self.prev_status == "break":
                self.start_break()
            self.prev_status = None
            return
        else:  # "not_stared" or "finished"
            self.reset()
            sleep(3)
            self.histories.append(["start_work", datetime.now(), "Opening"])
            self.status = "break"
            self.start_break(break_time)
        while True:
            print(self.status, self.work_timer, self.break_timer, self.total_working_timer)
            if self.status == "pause":
                self.is_lazy = False
                sleep(1)
                continue
            if self.status == "work":
                self.work_timer -= 1
                self.total_working_timer += 1
                if self.work_timer == -1:
                    self.work_timer = 1500
                    self.break_timer += 300
                self.is_lazy = False
            elif self.status == "break":
                self.break_timer -= 1
                if self.break_timer <= 0:
                    self.is_lazy = True
                    if (self.break_timer % 90 == 0) and (self.break_timer != 0):
                        try:
                            thread = threading.Thread(target=self.utils.call_me, name="callMe")
                            thread.start()
                        except BaseException:
                            print("Failed to call me")
            else:
                break
            sleep(1)
