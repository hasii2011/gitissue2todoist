
from typing import Callable
from typing import Dict
from typing import List
from typing import NewType

from dataclasses import dataclass
from dataclasses import field

from todoist_api_python.models import Project
from todoist_api_python.models import Task

@dataclass
class TaskInfo:
    slug:         str = ''
    gitIssueName: str = ''
    gitIssueURL:  str = ''
    labels:       List[str] = field(default_factory=list)

TaskInfoList = NewType('TaskInfoList', List[TaskInfo])

def taskInfoListFactory() -> TaskInfoList:
    return TaskInfoList([])

@dataclass
class CloneInformation:
    repositoryTask:    str = ''
    milestoneNameTask: str = ''
    tasksToClone:      TaskInfoList = field(default_factory=taskInfoListFactory)


Tasks             = List[Task]
ProjectName       = NewType('ProjectName', str)
ProjectDictionary = Dict[ProjectName, Project]


def tasksFactory() -> Tasks:
    return []


TaskName     = NewType('TaskName',     str)
TaskId       = NewType('TaskId',       str)
TaskNameMap  = NewType('TaskNameMap',  Dict[TaskName, TaskId])

@dataclass
class TodoistProgress:
    message:        str
    completedTasks: int
    totalTasks:     int

TodoistProgressCB = Callable[[TodoistProgress], None]
