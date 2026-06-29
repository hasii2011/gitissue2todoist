
from dataclasses import dataclass


@dataclass
class GitHubAuthorizationData:
    deviceCode:      str
    userCode:        str
    verificationUrl: str
    interval:        int
