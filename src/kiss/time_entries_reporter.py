import os
import sys
from typing import List

from kiss.clockify_api import ClockifyApi
from kiss.time_entries_checker import TimeEntriesCheckReport
from kiss.time_entries_diff import DaysTimeEntriesDiff, DayTimeEntriesDiff, TimeEntryDiff
from kiss.time_entries_file import DateTimeInterval
from kiss.user_settings import UserSettings
from kiss.utils import RESET_FORMAT, COLOR_YELLOW, COLOR_RED, COLOR_GREEN, BOLD, from_seconds_to_hours, from_seconds_to_days


class TimeEntriesReporter:
    api: ClockifyApi
    user_settings: UserSettings

    def __init__(self, api: ClockifyApi, user_settings: UserSettings):
        self.api = api
        self.user_settings = user_settings

    def create_report(self, time_entries_diff: DaysTimeEntriesDiff, report: TimeEntriesCheckReport) -> str:
        concatenated = []

        try:
            with open(self.get_logo_file()) as logo_file:
                concatenated.append(logo_file.read())
                concatenated.append('\n\n')
        except IOError as e:
            concatenated.append('')

        concatenated.append(self.create_days_report(time_entries_diff, report))
        concatenated.append('\n\n')

        if len(report.errors) > 0 or len(report.warnings) > 0:
            concatenated.append('==========\n')
            concatenated.append('= REPORT =\n')
            concatenated.append('==========\n\n')
            for error in report.errors:
                concatenated.append(f'{COLOR_RED}[ERROR]\t\t{error}{RESET_FORMAT}\n')

            for error in report.warnings:
                concatenated.append(f'{COLOR_YELLOW}[WARNING]\t{error}{RESET_FORMAT}\n')

        concatenated.append('===========\n')
        concatenated.append('= SUMMARY =\n')
        concatenated.append('===========\n\n')
        concatenated.append(f'{self.create_diff_summary(time_entries_diff)}\n')
        concatenated.append(f'{self.create_duration_summary(report)}\n')
        concatenated.append(f'{self.create_nb_public_holiday_summary(time_entries_diff)}\n')
        concatenated.append(f'{self.create_nb_personal_holiday_summary(time_entries_diff)}\n')

        return ''.join(concatenated)

    def get_logo_file(self):
        if getattr(sys, 'frozen', True):
            return f'{os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))}/logo.txt'
        else:
            return 'kiss/logo.txt'

    def create_days_report(self, time_entries_diff: DaysTimeEntriesDiff, report: TimeEntriesCheckReport) -> str:
        concatenated = []

        for day_time_entries in time_entries_diff.days:
            concatenated.append(f'{self.create_day_report(day_time_entries, report)}\n\n\n')

            if day_time_entries.day.day.weekday() == 6:
                concatenated.append(f'============\n')
                concatenated.append(f'= NEW WEEK =\n')
                concatenated.append(f'============\n\n\n')

        return ''.join(concatenated)

    def create_day_report(self, day_diff: DayTimeEntriesDiff, report: TimeEntriesCheckReport) -> str:
        entries_report = []

        for time_entry in self.sort_day_time_entries(day_diff.time_entries):
            entries_report.append(f'\t{self.create_time_entry_report(time_entry, report)}\n')

        entries_report_str = ''.join(entries_report)

        return f'{day_diff.day.day.strftime("%A")} {day_diff.day.day.__str__()}\n{entries_report_str}\n' \
               f'\tDuration in hour(s): {self.get_duration_string(day_diff, report)}'

    def create_time_entry_report(self, time_entries_diff: TimeEntryDiff, report: TimeEntriesCheckReport) -> str:
        status_string = self.get_time_entry_status_string(time_entries_diff)
        project_name: str
        task_name: str
        datetime_interval: DateTimeInterval
        description: str
        tag_names: List[str]
        check_flag = self.get_time_entry_check_flag(time_entries_diff, report)

        time_entry = time_entries_diff.time_entry
        if time_entry is not None:
            project_name = time_entry.project
            task_name = time_entry.task
            datetime_interval = time_entry.interval
            description = time_entry.description
            tag_names = time_entry.tags
        else:
            matching_entry = time_entries_diff.matching_entry

            project_name = self.get_project_name(matching_entry.project_id)
            task_name = self.get_task_name(matching_entry.project_id, matching_entry.task)
            datetime_interval = matching_entry.time_interval.as_datetime_interval()
            description = matching_entry.description
            tag_names = self.get_tag_names(matching_entry.tags)

        return f'[{status_string}]\t{project_name} - {task_name} "{description}" {tag_names}: ' \
               f'{datetime_interval} {check_flag}'

    def create_diff_summary(self, time_entries_diff: DaysTimeEntriesDiff) -> str:
        status = f'{BOLD}{COLOR_GREEN}YES{RESET_FORMAT}'
        for day_time_entry_diff in time_entries_diff.days:
            for time_entry_diff in day_time_entry_diff.time_entries:
                if time_entry_diff.is_to_add() or time_entry_diff.is_to_delete():
                    status = f'{BOLD}{COLOR_YELLOW}NO{RESET_FORMAT}'

        return f'Up-to-date with Clockify: {status}'

    def create_duration_summary(self, report: TimeEntriesCheckReport) -> str:
        status: str
        if len(report.days_duration_errors) > 0:
            status = f'{BOLD}{COLOR_RED}YES{RESET_FORMAT}'
        elif len(report.days_duration_warnings) > 0:
            status = f'{BOLD}{COLOR_YELLOW}YES{RESET_FORMAT}'
        else:
            status = f'{BOLD}{COLOR_GREEN}NO{RESET_FORMAT}'

        return f'Duration issue(s): {status}'

    def create_nb_public_holiday_summary(self, time_entries_diff: DaysTimeEntriesDiff) -> str:
        nb = 0

        for day_time_entries in time_entries_diff.days:
            for time_entry in day_time_entries.time_entries:
                generated_time_entry = time_entry.time_entry
                if (generated_time_entry is not None) and generated_time_entry.is_public_holiday(self.user_settings):
                    nb += generated_time_entry.get_time_entries_duration_in_secs()

        return f'Number public holidays in day(s): ' \
               f'{BOLD}{from_seconds_to_days(nb, self.user_settings.day.get_number_working_secs())}{RESET_FORMAT}'

    def create_nb_personal_holiday_summary(self, time_entries_diff: DaysTimeEntriesDiff) -> str:
        nb = 0

        for day_time_entries in time_entries_diff.days:
            for time_entry in day_time_entries.time_entries:
                generated_time_entry = time_entry.time_entry
                if (generated_time_entry is not None) and generated_time_entry.is_personal_holiday(self.user_settings):
                    nb += generated_time_entry.get_time_entries_duration_in_secs()

        return f'Number personal holidays in day(s): ' \
               f'{BOLD}{from_seconds_to_days(nb, self.user_settings.day.get_number_working_secs())}{RESET_FORMAT}'

    def sort_day_time_entries(self, entries: List[TimeEntryDiff]) -> List[TimeEntryDiff]:
        sorted_entries = entries.copy()
        sorted_entries.sort(key=
                            lambda time_entry_diff: (
                                time_entry_diff.get_time_interval_as_z_time().from_date,
                                self.get_time_entry_diff_sort_value(time_entry_diff)
                            ),
                            reverse=False
                            )

        return sorted_entries

    def get_time_entry_diff_sort_value(self, time_entry_diff: TimeEntryDiff):
        if time_entry_diff.is_to_keep():
            return 0
        if time_entry_diff.is_to_delete():
            return 1
        if time_entry_diff.is_to_add():
            return 2

    def get_project_name(self, project_id: str) -> str:
        if project_id is None:
            return None

        return self.api.get_project(project_id).name

    def get_task_name(self, project_id: str, task_id: str) -> str:
        if task_id is None:
            return None

        return self.api.get_project_task(project_id, task_id).name

    def get_tag_names(self, tag_ids: List[str]) -> List[str]:
        return [tag.name for tag in self.api.get_tags() if tag_ids.__contains__(tag.id)]

    def get_time_entry_status_string(self, time_entry_diff: TimeEntryDiff) -> str:
        if time_entry_diff.is_to_keep():
            return f'{BOLD}KEEP{RESET_FORMAT}'
        elif time_entry_diff.is_to_add():
            return f'{COLOR_GREEN}{BOLD}ADD{RESET_FORMAT}'
        elif time_entry_diff.is_to_delete():
            return f'{COLOR_RED}{BOLD}DEL{RESET_FORMAT}'
        else:
            raise Exception('Invalid state, cannot determine the status.')

    def get_duration_string(self, day_diff: DayTimeEntriesDiff, report: TimeEntriesCheckReport):
        hours = from_seconds_to_hours(day_diff.day.get_time_entries_duration_in_secs())
        if report.days_duration_errors.__contains__(day_diff.day.day):
            return f'{COLOR_RED}{hours}{RESET_FORMAT}'
        elif report.days_duration_warnings.__contains__(day_diff.day.day):
            return f'{COLOR_YELLOW}{hours}{RESET_FORMAT}'
        else:
            return hours

    def get_time_entry_check_flag(self, time_entries_diff: TimeEntryDiff, report: TimeEntriesCheckReport):
        if report.time_entry_errors.__contains__(time_entries_diff):
            return f'{COLOR_RED}{BOLD}* ERROR{RESET_FORMAT}'
        elif report.time_entry_warnings.__contains__(time_entries_diff):
            return f'{COLOR_YELLOW}{BOLD}* WARNING{RESET_FORMAT}'
        else:
            return ''
