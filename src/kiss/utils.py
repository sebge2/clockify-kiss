from datetime import datetime, time, timezone, date, timedelta

import pytz
import tzlocal

COLOR_GREEN = '\033[92m'
RESET_FORMAT = '\033[0m'
BOLD = '\033[1m'
COLOR_YELLOW = '\033[93m'
COLOR_RED = '\033[91m'


def parse_user_time(datetime_string: str) -> time:
    try:
        return datetime.strptime(datetime_string, '%H:%M:%S').time()
    except Exception as ex:
        raise Exception(f'Cannot parse time {datetime_string}: {ex}')


def parse_user_date(date_string: str) -> date:
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except Exception as ex:
        raise Exception(f'Cannot parse date {date_string}: {ex}')


def parse_user_datetime(datetime_string: str) -> datetime:
    try:
        return datetime.strptime(datetime_string, '%Y-%m-%d %X')
    except Exception as ex:
        raise Exception(f'Cannot parse datetime {datetime_string}: {ex}')


def parse_z_datetime(datetime_string: str) -> datetime:
    return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')


def from_datetime_to_zulu_string(day: datetime) -> str:
    return day.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def from_datetime_to_user(day: datetime) -> str:
    return day.strftime("%Y-%m-%d, %H:%M:%S")


def set_date_at_time(day: date, at_time: time) -> datetime:
    return datetime.combine(day, at_time)


def from_z_datetime_to_local(day: datetime) -> datetime:
    return day.replace(tzinfo=pytz.utc).astimezone(tzlocal.get_localzone())


def from_seconds_to_hours(seconds: int) -> str:
    return f'{seconds / 3600}'


def from_seconds_to_days(seconds: int, day_duration_in_sec: int):
    return seconds / day_duration_in_sec


def get_duration_in_secs(begin: datetime, end: datetime):
    start_delta = timedelta(hours=begin.hour, minutes=begin.minute, seconds=begin.second)
    end_delta = timedelta(hours=end.hour, minutes=end.minute, seconds=end.second)

    difference_delta = end_delta - start_delta

    return difference_delta.total_seconds()
