from typing import Dict
from typing import Iterator
from typing import NewType

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Project

from gitissue2todoist.preferences.Preferences import Preferences


PROJECT_SAFE_TO_DELETE:   str = 'NewProject-SafeToDelete'
BOGUS_SAFE_TO_DELETE:     str = 'Bogus-SafeToDelete'
MOCK_REPO_SAFE_TO_DELETE: str = 'MockRepo-SafeToDelete'

PROJECTS_TO_DELETE = [PROJECT_SAFE_TO_DELETE, BOGUS_SAFE_TO_DELETE, MOCK_REPO_SAFE_TO_DELETE]

ProjectName = str
ProjectId   = str

DeleteDictionary = NewType('DeleteDictionary', Dict[ProjectName, ProjectId])

# Used for prototyping


def getProjectsToDelete() -> DeleteDictionary:

    api_token: str        = Preferences().todoistAPIToken
    todoist:   TodoistAPI = TodoistAPI(api_token)

    deleteDictionary: DeleteDictionary = DeleteDictionary({})

    projectIter: Iterator = todoist.get_projects()
    for projects in projectIter:
        for p in projects:
            project: Project = p
            if project.name in PROJECTS_TO_DELETE:
                print(f'{project.name:25} - {project.id=}')
                deleteDictionary[project.name] = project.id

    return deleteDictionary

def deleteProjects(projectsToDelete: DeleteDictionary):
    api_token: str        = Preferences().todoistAPIToken
    todoist:   TodoistAPI = TodoistAPI(api_token)

    for projectName, projectId in projectsToDelete.items():
        print(f' Bye Bye --- {projectName:25} - {projectId=}')
        todoist.delete_project(project_id=projectId)


if __name__ == '__main__':
    projectsToBeDeleted: DeleteDictionary = getProjectsToDelete()
    print(f'{projectsToBeDeleted=}')

    deleteProjects(projectsToDelete=projectsToBeDeleted)
