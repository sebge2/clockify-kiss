from datetime import date
from typing import List

from .time_entries_diff import DaysTimeEntriesDiff, TimeEntryDiff
from .time_entries_generator import GeneratedTimeEntry
from .user_settings import UserSettings
from .utils import from_seconds_to_hours


class TimeEntriesCheckOption:
    partial: bool

    def __init__(self, partial: bool = None):
        self.partial = partial if partial is not None and partial is True else partial


class TimeEntriesCheckReport:
    days_duration_warnings: List[date]
    days_duration_errors: List[date]

    time_entry_warnings: List[TimeEntryDiff]
    time_entry_errors: List[TimeEntryDiff]

    errors: List[str]
    warnings: List[str]
    info: List[str]

    def __init__(self):
        self.days_duration_errors = []
        self.days_duration_warnings = []

        self.time_entry_errors = []
        self.time_entry_warnings = []

        self.errors = []
        self.warnings = []
        self.info = []

    def can_apply_diff(self) -> bool:
        return self.errors.__len__() == 0


class TimeEntriesChecker:
    user_settings: UserSettings
    option: TimeEntriesCheckOption

    def __init__(self, user_settings: UserSettings, option: TimeEntriesCheckOption):
        self.user_settings = user_settings
        self.option = option

    def generate_report(self, time_entries_diff: DaysTimeEntriesDiff) -> TimeEntriesCheckReport:
        report = TimeEntriesCheckReport()

        self.check_durations(time_entries_diff, report)
        self.check_no_overlap(time_entries_diff, report)
        self.check_personal_holidays(time_entries_diff, report)

        return report

    def check_durations(self, time_entries_diff: DaysTimeEntriesDiff, report: TimeEntriesCheckReport):
        for day_diff in time_entries_diff.days:
            diff_day = day_diff.day

            day_duration = diff_day.get_time_entries_duration_in_secs()
            working_day_expected_duration = self.user_settings.day.get_number_working_secs()

            if diff_day.is_working_day():
                if day_duration < working_day_expected_duration:
                    message = f'The day {diff_day.day} has only {from_seconds_to_hours(day_duration)} hour(s).'

                    report.days_duration_warnings.append(diff_day.day)

                    if self.option.partial:
                        report.warnings.append(message)
                    else:
                        report.errors.append(message)
                elif day_duration > working_day_expected_duration:
                    report.days_duration_warnings.append(diff_day.day)
                    report.warnings.append(
                        f'The day {diff_day.day} has exceeding time: {from_seconds_to_hours(day_duration)} hour(s).'
                    )
            else:
                if day_duration > 0:
                    report.warnings.append(
                        f'The day {diff_day.day} is not a working day, but has '
                        f'{from_seconds_to_hours(day_duration)} hour(s).'
                    )

    def check_personal_holidays(self,
                                time_entries_diff: DaysTimeEntriesDiff,
                                report: TimeEntriesCheckReport):
        day_settings = self.user_settings.day

        start_at = day_settings.start_at
        half_day_time = day_settings.get_half_day_time()
        end_at = day_settings.end_at

        for day_time_entry_diff in time_entries_diff.days:
            for time_entry_diff in day_time_entry_diff.time_entries:
                time_entry = time_entry_diff.time_entry

                if time_entry is not None and self.is_personal_holiday(time_entry):
                    start_time = time_entry.interval.from_date.time()
                    if (start_time != start_at) and (start_time != half_day_time):
                        report.time_entry_errors.append(time_entry_diff)
                        report.errors.append(f'The holiday {time_entry.interval} '
                                             f'must start at the beginning of the day ({start_at}), '
                                             f'or at half of the day ({half_day_time}).')

                    end_time = time_entry.interval.to_date.time()
                    if (end_time != end_at) and (end_time != half_day_time):
                        report.time_entry_errors.append(time_entry_diff)
                        report.errors.append(f'The holiday {time_entry.interval} '
                                             f'must end at the end of the day ({end_at}), '
                                             f'or at half of the day ({half_day_time}).')

    def check_no_overlap(self, time_entries_diff: DaysTimeEntriesDiff, report: TimeEntriesCheckReport):
        for day_diff in time_entries_diff.days:
            i = 0

            while i < len(day_diff.time_entries):
                j = 0
                while j < i:
                    first = day_diff.time_entries[i]
                    second = day_diff.time_entries[j]

                    j += 1

                    if (first.time_entry is not None) and \
                            (second.time_entry is not None) and \
                            first.time_entry.interval.overlap(second.time_entry.interval):
                        report.time_entry_errors.append(first)
                        report.time_entry_errors.append(second)

                        report.errors.append(f'The added time entry {first.time_entry.interval} '
                                             f'overlaps with the time entry: {second.time_entry.interval}')

                i += 1

    def is_personal_holiday(self, time_entry: GeneratedTimeEntry) -> bool:
        return time_entry.is_personal_holiday(self.user_settings)
