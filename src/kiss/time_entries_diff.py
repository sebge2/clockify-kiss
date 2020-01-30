from datetime import time
from typing import List

from .clockify_api import ClockifyApi
from .clockify_model import ClockifyTimeEntry
from .time_entries_file import DateTimeInterval
from .time_entries_generator import GeneratedDaysTimeEntries, GeneratedDayTimeEntries, GeneratedTimeEntry
from .user_settings import UserSettings
from .utils import from_datetime_to_zulu_string, set_date_at_time


class TimeEntryDiff:
    time_entry: GeneratedTimeEntry
    matching_entry: ClockifyTimeEntry

    def __init__(self, time_entry: GeneratedTimeEntry = None):
        self.time_entry = time_entry
        self.matching_entry = None

    def compare_with_existing_entry(self, existing_task: ClockifyTimeEntry) -> bool:
        return (self.time_entry.clockify_entry.workspaceId == existing_task.workspace_id) \
               and (self.time_entry.clockify_entry.user_id == existing_task.user_id) \
               and (self.time_entry.clockify_entry.project_id == existing_task.project_id) \
               and (self.time_entry.clockify_entry.task_id == existing_task.task) \
               and (self.time_entry.clockify_entry.tag_ids == existing_task.tags) \
               and (self.time_entry.clockify_entry.time_interval.start == existing_task.time_interval.start) \
               and (self.time_entry.clockify_entry.time_interval.end == existing_task.time_interval.end) \
               and (self.time_entry.clockify_entry.description == existing_task.description)

    def get_time_interval_as_z_time(self) -> DateTimeInterval:
        if self.matching_entry:
            return self.matching_entry.time_interval.as_datetime_interval()
        else:
            return self.time_entry.clockify_entry.time_interval.as_datetime_interval()

    def is_to_keep(self):
        if (self.time_entry is None) and (self.matching_entry is None):
            raise Exception('A generated time entry and/or an existing entry must be provided.')

        return self.matching_entry is not None and self.time_entry is not None

    def is_to_delete(self):
        if (self.time_entry is None) and (self.matching_entry is None):
            raise Exception('A generated time entry and/or an existing entry must be provided.')

        return self.time_entry is None

    def is_to_add(self):
        if (self.time_entry is None) and (self.matching_entry is None):
            raise Exception('A generated time entry and/or an existing entry must be provided.')

        return self.matching_entry is None


class DayTimeEntriesDiff:
    day: GeneratedDayTimeEntries
    time_entries: List[TimeEntryDiff]

    def __init__(self, day: GeneratedDayTimeEntries):
        self.day = day
        self.time_entries = [TimeEntryDiff(time_entry) for time_entry in day.time_entries]

    def add_existing_entry(self, existing: ClockifyTimeEntry):
        for time_entry in self.time_entries:
            if time_entry.time_entry is not None and time_entry.compare_with_existing_entry(existing):
                time_entry.matching_entry = existing
                return

        time_entry_diff = TimeEntryDiff()
        time_entry_diff.matching_entry = existing
        self.time_entries.append(time_entry_diff)


class DaysTimeEntriesDiff:
    days_time_entries: GeneratedDaysTimeEntries
    days: List[DayTimeEntriesDiff]

    def __init__(self, days_time_entries: GeneratedDaysTimeEntries):
        self.days_time_entries = days_time_entries
        self.days = []

        for day_time_entry in days_time_entries.get_days_time_entries():
            self.days.append(DayTimeEntriesDiff(day_time_entry))

    def add_existing_entry(self, existing: ClockifyTimeEntry):
        for day_time_entry in self.days:
            if day_time_entry.day.day == existing.time_interval.as_datetime_interval().from_date.date():
                day_time_entry.add_existing_entry(existing)
                return

        raise Exception(f'Cannot add time entry {existing.id}, there is no matching day')


class TimeEntriesDiffComputer:
    api: ClockifyApi
    user_settings: UserSettings

    def __init__(self, api: ClockifyApi, user_settings: UserSettings):
        self.api = api
        self.user_settings = user_settings

    def compute(self, days_time_entries: GeneratedDaysTimeEntries) -> DaysTimeEntriesDiff:
        days_time_entry_diff = DaysTimeEntriesDiff(days_time_entries)
        existing_time_entries = self.find_existing_entries(days_time_entries)

        for existing in existing_time_entries:
            days_time_entry_diff.add_existing_entry(existing)

        return days_time_entry_diff

    def apply(self, diff: DaysTimeEntriesDiff):
        for day_time_entries in diff.days:
            for time_entry in day_time_entries.time_entries:
                if time_entry.is_to_add():
                    self.api.add_time_entry(time_entry.time_entry.clockify_entry)
                if time_entry.is_to_delete():
                    self.api.delete_time_entry(time_entry.matching_entry.id, time_entry.matching_entry.workspace_id)

    def find_existing_entries(self, days_time_entries) -> List[ClockifyTimeEntry]:
        start = from_datetime_to_zulu_string(
            set_date_at_time(days_time_entries.interval.from_date, time(hour=0, minute=0, second=0)))
        end = from_datetime_to_zulu_string(
            set_date_at_time(days_time_entries.interval.to_date, time(hour=23, minute=59, second=59)))

        return self.api.find_time_entries(self.api.get_user().default_workspace, start, end)
