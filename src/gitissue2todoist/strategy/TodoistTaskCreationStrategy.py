
from enum import StrEnum


class TodoistTaskCreationStrategy(StrEnum):

    SINGLE_TODOIST_PROJECT      = 'Single Todoist Project'
    PROJECT_BY_REPOSITORY       = 'Project by Repository'
    ALL_ISSUES_ASSIGNED_TO_USER = 'All Issues Assigned to User'
    NOT_SET                     = 'Not Set'
