from enum import StrEnum


class MessageType(StrEnum):

    SELECTED_REPOSITORY_CHANGED = 'Selected Repository Changed'
    SELECTED_MILESTONE_CHANGED  = 'Selected Milestone Changed'
    CLONE_ISSUES                = 'Clone Issues'

    TASK_CREATION_COMPLETE      = 'Task Creation Complete'

    MULTIPLE_REPOSITORIES_SELECTED = 'Multiple Repositories Selected'
