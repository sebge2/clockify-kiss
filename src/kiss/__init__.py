import json
import os

import click

from .clockify_api import ClockifyApi
from .time_entries_checker import TimeEntriesChecker, TimeEntriesCheckOption
from .time_entries_diff import TimeEntriesDiffComputer
from .time_entries_file import TimeEntriesFile, Month, Task, DateInterval
from .time_entries_generator import TimeEntriesGenerator
from .time_entries_reporter import TimeEntriesReporter
from .user_settings import UserSettings

VERBOSE = False

config_file_path = '~/.clockify.cfg'
config_file = os.path.expanduser(config_file_path)
if os.path.exists(config_file):
    with open(config_file) as f:
        user_settings = UserSettings.load_user_settings(f.read())
else:
    raise Exception(f'Missing config file {config_file_path}')

api = ClockifyApi(user_settings)


#
# Technical
#
def default_serializer(o):
    return o.__dict__


def print_json(input_json):
    click.echo(json.dumps(input_json, indent=2, default=default_serializer))


#
# Commands
#
@click.command('user', short_help='Show current user')
def get_user():
    user = api.get_user()
    if VERBOSE:
        print_json(user)
    else:
        click.echo(f'{user.id}: {user.email}')


@click.command('workspaces', short_help='Show all workspaces')
def get_workspaces():
    workspaces = api.get_workspaces()
    if VERBOSE:
        print_json(workspaces)
    else:
        for i, workspace in enumerate(workspaces):
            click.echo(f'{workspace.id}: {workspace.name}')


@click.command('projects', short_help='Show all workspace projects')
@click.option('-w', '--workspace', 'workspace')
@click.option('-n', '--name', 'name')
def get_projects(workspace, name):
    if name is not None:
        projects = api.get_projects_by_name(name, workspace)
    else:
        projects = api.get_projects(workspace)

    if VERBOSE:
        print_json(projects)
    else:
        for project in projects:
            click.echo(f'{project.id}: {project.name}')


@click.command('tags', short_help='Show all workspace tags')
@click.option('-w', '--workspace', 'workspace')
@click.option('-n', '--name', 'name')
def get_tags(workspace, name):
    if name is not None:
        tags = api.get_tags_by_name(name, workspace)
    else:
        tags = api.get_tags(workspace)

    if VERBOSE:
        print_json(tags)
    else:
        for tag in tags:
            click.echo(f'{tag.id}: {tag.name}')


@click.command('project-tasks', short_help='Show all tasks of a project')
@click.option('-w', '--workspace', 'workspace')
@click.option('-n', '--name', 'name')
@click.argument('project')
def get_tasks(workspace, project, name):
    tasks: []
    if name is not None:
        tasks = api.get_project_task_by_name(project, name, workspace)
    else:
        tasks = api.get_project_tasks(project, workspace)

    if VERBOSE:
        print_json(tasks)
    else:
        for i, task in enumerate(tasks):
            click.echo(f'{task.id}: {task.name}')


@click.command('time-entries', short_help='Find time entries')
@click.option('-w', '--workspace', 'workspace')
@click.option('-s', '--start', 'start')
@click.option('-e', '--end', 'end')
def find_time_entries(workspace, start, end):
    entries = api.find_time_entries(workspace, start, end)
    if VERBOSE:
        print_json(entries)
    else:
        for i, entry in enumerate(entries):
            click.echo(f'{entry.id}: {entry.description}')


@click.command('fill-time-entries', short_help='Fill time entries a period')
@click.argument('file')
@click.option('--partial', is_flag=True, help="Specify that the time entries are partially completed", required=False)
def fill_entries(file, partial: bool = None):
    with open(file) as jsonFile:
        time_entries = TimeEntriesFile.load_time_entries(jsonFile.read())

        generator = TimeEntriesGenerator(time_entries, api, user_settings)
        tasks_diff_computer = TimeEntriesDiffComputer(api, user_settings)
        reporter = TimeEntriesReporter(api, user_settings)
        checker = TimeEntriesChecker(user_settings, TimeEntriesCheckOption(partial))

        days_tasks = generator.generate()

        tasks_diff = tasks_diff_computer.compute(days_tasks)

        check_report = checker.generate_report(tasks_diff)

        print(reporter.create_report(tasks_diff, check_report))

        if check_report.can_apply_diff() is False:
            exit(1)

        if click.confirm('Do you want to apply those time entries?', abort=True):
            tasks_diff_computer.apply(tasks_diff)


@click.group()
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def cli(verbose):
    global VERBOSE
    VERBOSE = verbose


#
# Commands Registration
#
cli.add_command(get_user)
cli.add_command(get_workspaces)
cli.add_command(get_projects)
cli.add_command(get_tags)
cli.add_command(get_tasks)
cli.add_command(find_time_entries)
cli.add_command(fill_entries)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
