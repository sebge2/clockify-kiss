import json
from datetime import date
from datetime import datetime
from typing import List

from src.kiss.utils import from_datetime_to_user, parse_user_date, parse_user_datetime


class Month:
    year: int
    month: int

    def __init__(self, year: int, month: int):
        self.year = year
        self.month = month


class DateInterval:
    from_date: date
    to_date: date

    def __init__(self, from_date: date, to_date: date):
        self.from_date = from_date
        self.to_date = to_date

    def __str__(self):
        return f'{self.from_date} => {self.to_date}'

    def include(self, day: date):
        return self.from_date <= day <= self.to_date

    @staticmethod
    def parse_from_dict(dic: dict):
        return DateInterval(parse_user_date(dic['fromDate']), parse_user_date(dic['toDate']))


class DateTimeInterval:
    from_date: datetime
    to_date: datetime

    def __init__(self, from_date: datetime, to_date: datetime):
        if from_date > to_date:
            raise Exception(f'The starting date {from_date} cannot be after the end date {to_date}')

        self.from_date = from_date
        self.to_date = to_date

    def overlap(self, other):
        return ((self.from_date >= other.from_date) and (self.to_date <= other.to_date)) \
               or ((other.from_date >= self.from_date) and (other.to_date <= self.to_date))

    def __str__(self):
        return f'[{from_datetime_to_user(self.from_date)} => {from_datetime_to_user(self.to_date)}]'

    @staticmethod
    def parse_from_dict(dic: dict):
        return DateTimeInterval(parse_user_datetime(dic['fromDate']), parse_user_datetime(dic['toDate']))


class PersonalHoliday:
    interval: DateTimeInterval

    def __init__(self, interval: DateTimeInterval):
        self.interval = interval

    @staticmethod
    def parse_from_dict(dic: dict):
        return PersonalHoliday(DateTimeInterval.parse_from_dict(dic['interval']))


class DefaultTask:
    project: str
    task: str
    interval: DateInterval
    description: str
    tags: List[str]

    def __init__(self, project: str, task: str, interval: DateInterval, description: str, tags: List[str]):
        self.project = project
        self.task = task
        self.interval = interval
        self.description = description
        self.tags = tags

    @staticmethod
    def parse_from_dict(task: dict):
        return DefaultTask(
            task['project'],
            task['task'] if task.__contains__('task') else None,
            DateInterval.parse_from_dict(task['interval']),
            task['description'] if task.__contains__('description') else None,
            task['tags']
        )


class Task:
    project: str
    task: str
    interval: DateTimeInterval
    description: str
    tags: List[str]

    def __init__(self, project: str, task: str, interval: DateTimeInterval, description: str, tags: List[str]):
        self.project = project
        self.task = task
        self.interval = interval
        self.description = description
        self.tags = tags

    @staticmethod
    def parse_from_dict(task: dict):
        return Task(
            task['project'],
            task['task'] if task.__contains__('task') else None,
            DateTimeInterval.parse_from_dict(task['interval']),
            task['description'] if task.__contains__('description') else None,
            task['tags']
        )


class TimeEntriesFile:
    period: DateInterval
    personal_holidays: List[PersonalHoliday]
    public_holidays: List[date]
    tasks: List[Task]
    default_tasks: List[DefaultTask]

    def __init__(self, period: DateInterval):
        self.period = period
        self.personal_holidays = []
        self.public_holidays = []
        self.tasks = []
        self.default_tasks = []

    @staticmethod
    def load_time_entries(file_content):
        dic = json.loads(file_content)

        time_entries = TimeEntriesFile(DateInterval.parse_from_dict(dic['period']))

        for public_holiday in dic['publicHolidays']:
            time_entries.public_holidays.append(parse_user_date(public_holiday))

        for personal_holiday in dic['personalHolidays']:
            time_entries.personal_holidays.append(PersonalHoliday.parse_from_dict(personal_holiday))

        for task in dic['tasks']:
            time_entries.tasks.append(Task.parse_from_dict(task))

        for default_task in dic['defaultTasks']:
            time_entries.default_tasks.append(DefaultTask.parse_from_dict(default_task))

        return time_entries
