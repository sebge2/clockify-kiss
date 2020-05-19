import uuid
from datetime import date, timedelta, datetime, time
from typing import List

from kiss.clockify_api import ClockifyApi
from kiss.clockify_model import ClockifyTimeNewEntry, ClockifyTimeInterval
from kiss.time_entries_file import TimeEntriesFile, DateTimeInterval, DateInterval
from kiss.user_settings import DaySettings
from kiss.user_settings import UserSettings
from kiss.utils import from_datetime_to_zulu_string, set_date_at_time, get_duration_in_secs


class GeneratedTimeEntry:
    project: str
    task: str
    description: str
    interval: DateTimeInterval
    tags: List[str]
    clockify_entry: ClockifyTimeNewEntry

    def __init__(self,
                 project: str,
                 task: str,
                 description: str,
                 interval: DateTimeInterval,
                 tags: [],
                 clockify_entry: ClockifyTimeNewEntry):
        self.project = project
        self.task = task
        self.description = description
        self.interval = interval
        self.tags = tags
        self.clockify_entry = clockify_entry

    def get_time_entries_duration_in_secs(self):
        return get_duration_in_secs(self.interval.from_date, self.interval.to_date)

    def is_personal_holiday(self, user_settings: UserSettings) -> bool:
        return (self.project == user_settings.personal_holiday.project) and \
               (self.task == user_settings.personal_holiday.task)

    def is_public_holiday(self, user_settings: UserSettings) -> bool:
        return (self.project == user_settings.public_holiday.project) and \
               (self.task == user_settings.public_holiday.task)


class GeneratedDayTimeEntries:
    day: date
    time_entries: List[GeneratedTimeEntry]

    def __init__(self, day: date):
        self.day = day
        self.time_entries = []

    def add_time_entry(self, new_time_entry: GeneratedTimeEntry) -> None:
        closest_to = self.find_time_entry_closest_to(new_time_entry.interval.to_date)

        if closest_to is None:
            self.time_entries.append(new_time_entry)
        else:
            self.time_entries.insert(self.time_entries.index(closest_to), new_time_entry)

    def find_time_entry_closest_to(self, start_date: datetime) -> GeneratedTimeEntry:
        closest = None

        for time_entry in self.time_entries:
            if (closest is None or closest.interval.from_date >= time_entry.interval.from_date) and (
                    time_entry.interval.from_date >= start_date):
                closest = time_entry

        return closest

    def is_working_day(self) -> bool:
        return self.day.weekday() < 5

    def get_time_entries_duration_in_secs(self) -> int:
        duration = 0
        for time_entry in self.time_entries:
            duration += time_entry.get_time_entries_duration_in_secs()

        return duration


class GeneratedDaysTimeEntries:
    interval: DateInterval
    days = {}

    def __init__(self, interval: DateInterval):
        self.interval = interval

    def get_or_create(self, day: date) -> GeneratedDayTimeEntries:
        if self.interval.include(day) is False:
            raise Exception(f'The date {date} is not included in {self.interval}')

        if not self.days.__contains__(day):
            self.days[day] = GeneratedDayTimeEntries(day)

        return self.days[day]

    def get_days_time_entries(self) -> List[GeneratedDayTimeEntries]:
        array = [self.days[day] for day in self.days]
        array.sort(key=lambda day_time_entries: day_time_entries.day, reverse=False)

        return array

    def get_day_time_entries_duration_in_secs(self, day: date) -> int:
        return self.get_or_create(day).get_time_entries_duration_in_secs()


class TimeEntriesGenerator:
    time_entries_file: TimeEntriesFile
    user_settings: UserSettings
    api: ClockifyApi

    def __init__(self, time_entries_file: TimeEntriesFile, api: ClockifyApi, user_settings: UserSettings):
        self.time_entries_file = time_entries_file
        self.api = api
        self.user_settings = user_settings

    def generate(self) -> GeneratedDaysTimeEntries:
        days_time_entries: GeneratedDaysTimeEntries = self.initialize_day_time_entries()
        self.generate_time_entries(days_time_entries)

        return days_time_entries

    def initialize_day_time_entries(self) -> GeneratedDaysTimeEntries:
        period_interval = self.time_entries_file.period
        day_time_entries = GeneratedDaysTimeEntries(period_interval)

        for current_date in self.generate_days(period_interval.from_date, period_interval.to_date):
            day_time_entries.get_or_create(current_date)

        return day_time_entries

    def generate_time_entries(self, days_time_entries: GeneratedDaysTimeEntries):
        self.generate_public_holidays_time_entries(days_time_entries)
        self.generate_personal_holidays_time_entries(days_time_entries)
        self.generate_specific_time_entries(days_time_entries)
        self.generate_default_time_entries(days_time_entries)

    def get_project_id(self, project_name: str) -> str:
        projects = self.api.get_projects_by_name(project_name)

        if projects.__len__() != 1:
            raise Exception(
                f'One and only project must match the name [{project_name}], but {projects.__len__()} found.')

        return projects[0].id

    def get_task_id(self, project_name: str, task_name: str) -> str:
        if task_name is None:
            return None

        tasks = self.api.get_project_task_by_name(self.get_project_id(project_name), task_name)

        if tasks.__len__() != 1:
            raise Exception(f'One and only task must match the name [{task_name}], but {tasks.__len__()} found.')

        return tasks[0].id

    def get_tag_ids(self, tag_names: []) -> List[str]:
        tag_ids = []
        for tag in self.api.get_tags():
            if tag_names.__contains__(tag.name):
                tag_ids.append(tag.id)

        return tag_ids

    def create_time_entry(self,
                          project: str,
                          task: str,
                          description: str,
                          interval: DateTimeInterval,
                          tag_names: List[str]) -> GeneratedTimeEntry:
        return GeneratedTimeEntry(
            project,
            task,
            description,
            interval,
            tag_names,
            ClockifyTimeNewEntry(
                uuid.uuid1().__str__(),
                description if description is not None else 'TASK',
                self.get_project_id(project),
                self.api.get_user().id,
                self.get_task_id(project, task),
                self.get_tag_ids(tag_names),
                ClockifyTimeInterval(
                    from_datetime_to_zulu_string(interval.from_date),
                    from_datetime_to_zulu_string(interval.to_date)
                ),
                self.api.get_user().default_workspace
            )
        )

    def generate_public_holidays_time_entries(self, day_time_entries: GeneratedDaysTimeEntries):
        for public_holiday in self.time_entries_file.public_holidays:
            day_time_entries.get_or_create(public_holiday).add_time_entry(
                self.create_time_entry(
                    self.user_settings.public_holiday.project,
                    self.user_settings.public_holiday.task,
                    self.user_settings.public_holiday.description,
                    self.generate_interval_start_and_end(
                        public_holiday,
                        self.user_settings.day.start_at,
                        self.user_settings.day.end_at
                    ),
                    self.user_settings.public_holiday.tags
                )
            )

    def generate_personal_holidays_time_entries(self, day_time_entries: GeneratedDaysTimeEntries):
        for personal_holiday in self.time_entries_file.personal_holidays:
            personal_holiday_days = self.split_datetime_interval(personal_holiday.interval, self.user_settings.day)
            for day in personal_holiday_days:
                if day_time_entries.get_or_create(day.from_date.date()).get_time_entries_duration_in_secs() == 0:
                    day_time_entries.get_or_create(day.from_date.date()).add_time_entry(
                        self.create_time_entry(
                            self.user_settings.personal_holiday.project,
                            self.user_settings.personal_holiday.task,
                            self.user_settings.personal_holiday.description,
                            day,
                            self.user_settings.personal_holiday.tags
                        )
                    )

    def generate_specific_time_entries(self, day_time_entries: GeneratedDaysTimeEntries):
        for task in self.time_entries_file.tasks:
            task_days = self.split_datetime_interval(task.interval, self.user_settings.day)
            for day in task_days:
                day_time_entries.get_or_create(day.from_date.date()).add_time_entry(
                    self.create_time_entry(
                        task.project,
                        task.task,
                        task.description,
                        day,
                        task.tags
                    )
                )

    def generate_default_time_entries(self, days_time_entries: GeneratedDaysTimeEntries):
        for default_task in self.time_entries_file.default_tasks:
            days = self.split_date_interval(default_task.interval, self.user_settings.day)
            for day in days:
                day_time_entries = days_time_entries.get_or_create(day.from_date.date())

                if day_time_entries.is_working_day():
                    for missing_interval in self.find_missing_interval(day_time_entries):
                        day_time_entries.add_time_entry(
                            self.create_time_entry(
                                default_task.project,
                                default_task.task,
                                default_task.description,
                                missing_interval,
                                default_task.tags
                            )
                        )

    def split_datetime_interval(self, interval: DateTimeInterval, day_settings: DaySettings) -> List[DateTimeInterval]:
        split = []

        if interval.from_date.day == interval.to_date.day:
            split.append(interval)
            return split

        split.append(self.generate_interval_end(interval, day_settings.end_at))

        for current_date in self.generate_days(interval.from_date.date(),
                                               interval.to_date.date().__add__(timedelta(days=-1))):
            split.append(self.generate_interval_start_and_end(current_date, day_settings.start_at, day_settings.end_at))

        split.append(self.generate_interval_start(interval, day_settings.start_at))

        return split

    def split_date_interval(self, interval: DateInterval, day_settings: DaySettings) -> List[DateTimeInterval]:
        split = []

        if interval.from_date.day == interval.to_date.day:
            split.append(interval)
            return split

        split.append(self.generate_interval_start_and_end(interval.from_date, day_settings.start_at, day_settings.end_at))

        for current_date in self.generate_days(interval.from_date,
                                               interval.to_date.__add__(timedelta(days=-1))):
            split.append(self.generate_interval_start_and_end(current_date, day_settings.start_at, day_settings.end_at))

        split.append(self.generate_interval_start_and_end(interval.to_date, day_settings.start_at, day_settings.end_at))

        return split

    def find_missing_interval(self, day_time_entries: GeneratedDayTimeEntries) -> List[DateTimeInterval]:
        intervals = []

        if day_time_entries.get_time_entries_duration_in_secs() >= self.user_settings.day.get_number_working_secs():
            return intervals

        current_start_date = datetime.combine(day_time_entries.day, self.user_settings.day.start_at)

        while current_start_date.time() < self.user_settings.day.end_at:
            closest = day_time_entries.find_time_entry_closest_to(current_start_date)

            if closest is not None:
                if closest.interval.from_date == current_start_date:
                    current_start_date = closest.interval.to_date
                else:
                    intervals.append(DateTimeInterval(current_start_date, closest.interval.from_date))
                    current_start_date = closest.interval.to_date
            else:
                end_date = datetime.combine(day_time_entries.day, self.user_settings.day.end_at)
                intervals.append(DateTimeInterval(current_start_date, end_date))
                current_start_date = end_date

        return intervals

    def generate_days(self, from_date: date, to_date: date) -> List[date]:
        num_days = (to_date - from_date).days + 1

        if num_days < 0:
            return []

        return [from_date.__add__(timedelta(days=i)) for i in range(num_days)]

    def generate_interval_start(self, interval: DateTimeInterval, start_at: time) -> DateTimeInterval:
        return DateTimeInterval(
            datetime.combine(interval.to_date, start_at),
            interval.to_date,
        )

    def generate_interval_end(self, interval: DateTimeInterval, end_at: time) -> DateTimeInterval:
        return DateTimeInterval(
            interval.from_date,
            datetime.combine(interval.from_date, end_at)
        )

    def generate_interval_start_and_end(self, current_date, start_at: time, end_at: time) -> DateTimeInterval:
        return DateTimeInterval(
            set_date_at_time(current_date, start_at),
            set_date_at_time(current_date, end_at)
        )
