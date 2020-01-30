import json
from datetime import time, timedelta, datetime, date
from typing import List

from .utils import parse_user_time


class TaskSettings:
    project: str
    task: str
    description: str
    tags: List[str]

    def __init__(self, project: str, task: str, description: str, tags: List[str]):
        self.project = project
        self.task = task
        self.description = description
        self.tags = tags

    @staticmethod
    def parse_from_dict(dic: dict):
        return TaskSettings(dic['project'], dic['task'], dic['description'], dic['tags'])


class DaySettings:
    start_at: time
    end_at: time

    def __init__(self, start_at: time, end_at: time):
        self.start_at = start_at
        self.end_at = end_at

    def get_number_working_secs(self):
        start = timedelta(hours=self.start_at.hour, minutes=self.start_at.minute, seconds=self.start_at.second)
        end = timedelta(hours=self.end_at.hour, minutes=self.end_at.minute, seconds=self.end_at.second)

        difference_delta = end - start

        return difference_delta.total_seconds()

    def get_half_day_time(self):
        duration = self.get_number_working_secs()

        return (datetime.combine(date.today(), self.start_at) + timedelta(seconds= duration/2)).time()

    @staticmethod
    def parse_from_dict(dic: dict):
        return DaySettings(parse_user_time(dic['startAt']), parse_user_time(dic['endAt']))


class UserSettings:
    token: str
    public_holiday: TaskSettings
    personal_holiday: TaskSettings
    day: DaySettings

    def __init__(self, token: str, public_holiday: TaskSettings, personal_holiday: TaskSettings, day: DaySettings):
        self.token = token
        self.public_holiday = public_holiday
        self.personal_holiday = personal_holiday
        self.day = day

    @staticmethod
    def load_user_settings(file_content):
        dic = json.loads(file_content)

        return UserSettings(
            dic['token'],
            TaskSettings.parse_from_dict(dic['publicHoliday']),
            TaskSettings.parse_from_dict(dic['personalHoliday']),
            DaySettings.parse_from_dict(dic['day'])
        )
