import json
import re
from typing import List

import requests

from kiss.clockify_model import ClockifyWorkspace, ClockifyProject, ClockifyTimeEntry, ClockifyTask, ClockifyUser, \
    ClockifyTag, ClockifyTimeNewEntry
from kiss.user_settings import UserSettings

ENDPOINT = "https://api.clockify.me/api/v1/"


class ClockifyApi:
    headers: object

    cached_user: ClockifyUser = None
    cached_workspaces = []
    cached_workspace_projects = {}
    cached_workspace_tags = {}
    cached_project_tasks = {}

    def __init__(self, user_settings: UserSettings):
        self.headers = {"X-Api-Key": user_settings.token, "content-type": "application/json"}

    def get_user(self) -> ClockifyUser:
        if self.cached_user is not None:
            return self.cached_user

        r = requests.get(ENDPOINT + '/user', headers=self.headers)
        if r.status_code != 200:
            raise Exception(f'Error while retrying the current user. Returned message: {r.json()["message"]}, '
                            f'status code: {r.status_code}.')

        self.cached_user = ClockifyUser.map(r.json())

        return self.cached_user

    def get_workspaces(self) -> List[ClockifyWorkspace]:
        if self.cached_workspaces.__len__() > 0:
            return self.cached_workspaces

        r = requests.get(ENDPOINT + 'workspaces/', headers=self.headers)
        if r.status_code != 200:
            raise Exception(f'Error while retrying workspaces. Returned message: {r.json()["message"]}, '
                            f'status code: {r.status_code}.')

        self.cached_workspaces = [ClockifyWorkspace.map(workspace) for workspace in r.json()]

        return self.cached_workspaces

    def get_projects(self, workspace: str = None) -> List[ClockifyProject]:
        if workspace is None:
            workspace = self.get_user().default_workspace

        if self.cached_workspace_projects.__contains__(workspace):
            return self.cached_workspace_projects[workspace]

        r = requests.get(ENDPOINT + f'workspaces/{workspace}/projects/?page-size=100', headers=self.headers)
        if r.status_code != 200:
            raise Exception(f'Error while retrying projects. Returned message: {r.json()["message"]}, '
                            f'status code: {r.status_code}.')

        self.cached_workspace_projects[workspace] = [ClockifyProject.map(project) for project in r.json()]

        return self.cached_workspace_projects[workspace]

    def get_projects_by_name(self, project_name: str, workspace: str = None) -> List[ClockifyProject]:
        pattern = re.compile(project_name)
        return [project for project in self.get_projects(workspace) if pattern.match(project.name) is not None]

    def get_project(self, project_id: str, workspace: str = None) -> ClockifyProject:
        projects = [project for project in self.get_projects(workspace) if project_id == project.id]

        if projects.__len__() != 1:
            raise Exception(f'One and one project is expected for the id {project_id}, but found {projects.__len__()}')

        return projects[0]

    def get_tags(self, workspace: str = None) -> List[ClockifyTag]:
        if workspace is None:
            workspace = self.get_user().default_workspace

        if self.cached_workspace_tags.__contains__(workspace):
            return self.cached_workspace_tags[workspace]

        r = requests.get(ENDPOINT + f'workspaces/{workspace}/tags/', headers=self.headers)
        if r.status_code != 200:
            raise Exception(f'Error while retrying tags. Returned message: {r.json()["message"]}, '
                            f'status code: {r.status_code}.')

        self.cached_workspace_tags[workspace] = [ClockifyTag.map(tag) for tag in r.json()]

        return self.cached_workspace_tags[workspace]

    def get_tags_by_name(self, tag_name: str, workspace: str = None) -> List[ClockifyTag]:
        pattern = re.compile(tag_name)
        return [tag for tag in self.get_tags(workspace) if pattern.match(tag.name) is not None]

    def get_project_tasks(self, project: str, workspace: str = None) -> List[ClockifyTask]:
        if workspace is None:
            workspace = self.get_user().default_workspace

        if self.cached_project_tasks.__contains__(project):
            return self.cached_project_tasks[project]

        r = requests.get(ENDPOINT + f'workspaces/{workspace}/projects/{project}/tasks', headers=self.headers)
        if r.status_code != 200:
            raise Exception(f'Error while retrying tasks. Returned message: {r.json()["message"]}, '
                            f'status code: {r.status_code}.')

        self.cached_project_tasks[project] = [ClockifyTask.map(task) for task in r.json()]

        return self.cached_project_tasks[project]

    def get_project_task(self, project_id: str, task_id: str, workspace: str = None) -> ClockifyTask:
        tasks = [task for task in self.get_project_tasks(project_id, workspace) if task.id == task_id]

        if tasks.__len__() != 1:
            raise Exception(f'One and one task is expected for the id {project_id}, but found {tasks.__len__()}')

        return tasks[0]

    def get_project_task_by_name(self, project: str, task_name: str, workspace: str = None) -> List[ClockifyTask]:
        pattern = re.compile(task_name)
        return [task for task in self.get_project_tasks(project, workspace) if pattern.match(task.name) is not None]

    def find_time_entries(self, workspace: str = None, start: str = None, end: str = None) -> List[ClockifyTimeEntry]:
        if workspace is None:
            workspace = self.get_user().default_workspace

        user = self.get_user().id

        url = ENDPOINT + f'workspaces/{workspace}/user/{user}/time-entries'
        query_params = {}

        if start is not None:
            query_params['start'] = start

        if end is not None:
            query_params['end'] = end

        r = requests.get(url, headers=self.headers, params=query_params)
        if r.status_code != 200:
            raise Exception(f'Error while retrying time entries. '
                            f'Returned message: {r.json()["message"]}, status code: {r.status_code}.')

        return [ClockifyTimeEntry.map(entry) for entry in r.json()]

    def add_time_entry(self, time_entry: ClockifyTimeNewEntry) -> ClockifyTimeEntry:
        url = ENDPOINT + f'/workspaces/{time_entry.workspaceId}/time-entries'
        r = requests.post(url, json.dumps(time_entry.__dict__()), headers=self.headers)

        if r.status_code != 201:
            raise Exception(f'Error while adding a time entry. '
                            f'Returned message: {r.json()["message"]}, status code: {r.status_code}.')

        return ClockifyTimeEntry.map(r.json())

    def delete_time_entry(self, time_entry_id: str, workspace_id: str = None):
        if workspace_id is None:
            workspace_id = self.get_user().default_workspace

        url = ENDPOINT + f'/workspaces/{workspace_id}/time-entries/{time_entry_id}'
        r = requests.delete(url, headers=self.headers)

        if r.status_code != 204:
            raise Exception(f'Error while deleting a time entry. '
                            f'Returned message: {r.json()["message"]}, status code: {r.status_code}.')
