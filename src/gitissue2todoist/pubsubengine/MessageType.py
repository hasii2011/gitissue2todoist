from enum import StrEnum


class MessageType(StrEnum):

    SELECTED_REPOSITORY_CHANGED = 'Selected Repository Changed'
    SELECTED_MILESTONE_CHANGED  = 'Selected Milestone Changed'
    CLONE_ISSUES                 = 'Clone Issues'
