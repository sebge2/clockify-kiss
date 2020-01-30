from typing import List

from .time_entries_file import DateTimeInterval
from .utils import from_z_datetime_to_local, parse_z_datetime


class ClockifyTimeInterval:
    start: str
    end: str

    def __init__(self,
                 start: str,
                 end: str):
        self.start = start
        self.end = end

    def as_datetime_interval(self) -> DateTimeInterval:
        return DateTimeInterval(
            from_z_datetime_to_local(parse_z_datetime(self.start)),
            from_z_datetime_to_local(parse_z_datetime(self.end))
        )

    @staticmethod
    def map(json):
        return ClockifyTimeInterval(json['start'], json['end'])


class ClockifyUser:
    id: str
    email: str
    default_workspace: str

    def __init__(self,
                 id: str,
                 email: str,
                 default_workspace: str):
        self.id = id
        self.email = email
        self.default_workspace = default_workspace

    @staticmethod
    def map(user):
        return ClockifyUser(user['id'], user['email'], user['defaultWorkspace'])


class ClockifyWorkspace:
    id: str
    name: str

    def __init__(self,
                 id: str,
                 name: str):
        self.id = id
        self.name = name

    @staticmethod
    def map(workspace):
        return ClockifyWorkspace(workspace['id'], workspace['name'])


class ClockifyProject:
    id: str
    name: str
    archived: bool

    def __init__(self,
                 id: str,
                 name: str,
                 archived: bool):
        self.id = id
        self.name = name
        self.archived = archived

    @staticmethod
    def map(project):
        return ClockifyProject(project["id"], project["name"], project['archived'])


class ClockifyTag:
    id: str
    name: str
    workspace_id: str

    def __init__(self,
                 id: str,
                 name: str,
                 workspace_id: str):
        self.id = id
        self.name = name
        self.workspace_id = workspace_id

    @staticmethod
    def map(tag):
        return ClockifyTag(tag["id"], tag["name"], tag['workspaceId'])


class ClockifyTask:
    id: str
    name: str
    project_id: str
    status: str
    assignee_ids: List[str]

    def __init__(self,
                 id: str,
                 name: str,
                 project_id: str,
                 status: str,
                 assignee_ids: List[str]):
        self.id = id
        self.name = name
        self.project_id = project_id
        self.status = status
        self.assignee_ids = assignee_ids

    @staticmethod
    def map(task):
        return ClockifyTask(task["id"], task["name"], task['projectId'], task['status'], task['assigneeIds'])


class ClockifyTimeEntry:
    id: str
    description: str
    project_id: str
    tags: List[str]
    task: str
    time_interval: ClockifyTimeInterval
    workspace_id: str
    user_id: str

    def __init__(self,
                 id: str,
                 description: str,
                 project_id: str,
                 tags: List[str],
                 task: str,
                 time_interval: ClockifyTimeInterval,
                 workspace_id: str,
                 user_id: str):
        self.id = id
        self.description = description
        self.project_id = project_id
        self.tags = tags
        self.task = task
        self.time_interval = time_interval
        self.workspace_id = workspace_id
        self.user_id = user_id

    @staticmethod
    def map(entry):
        return ClockifyTimeEntry(
            entry["id"],
            entry["description"],
            entry['projectId'],
            entry['tagIds'],
            entry['taskId'],
            ClockifyTimeInterval.map(entry['timeInterval']),
            entry['workspaceId'],
            entry['userId']
        )


class ClockifyTimeNewEntry:
    id: str
    description: str
    project_id: str
    user_id: str
    task_id: str
    tag_ids: List[str]
    time_interval: ClockifyTimeInterval
    workspaceId: str

    def __init__(self,
                 id: str,
                 description: str,
                 project_id: str,
                 user_id: str,
                 task_id: str,
                 tag_ids: List[str],
                 time_interval: ClockifyTimeInterval,
                 workspace_id: str):
        self.id = id
        self.description = description
        self.project_id = project_id
        self.user_id = user_id
        self.task_id = task_id
        self.tag_ids = tag_ids
        self.time_interval = time_interval
        self.workspaceId = workspace_id

    def __dict__(self):
        return {
            'id': self.id,
            'description': self.description,
            'projectId': self.project_id,
            'userId': self.user_id,
            'taskId': self.task_id,
            'tagIds': self.tag_ids,
            'workspaceId': self.workspaceId,
            'start': self.time_interval.start,
            'end': self.time_interval.end,
            'timeInterval': {
                'start': self.time_interval.start,
                'end': self.time_interval.end
            }
        }
