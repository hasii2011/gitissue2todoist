
from typing import TypedDict
from typing import NotRequired

from asyncio import sleep

from requests import Response
from requests import post

from webbrowser import open as webBrowserOpen

from gitissue2todoist.githubauth.GitHubAuthorizationData import GitHubAuthorizationData

DF_SLOW_DOWN:             str = 'slow_down'
DF_AUTHORIZATION_PENDING: str = 'authorization_pending'

GITHUB_KEY_DEVICE_CODE:      str = 'device_code'
GITHUB_KEY_USER_CODE:        str = 'user_code'
GITHUB_KEY_VERIFICATION_URI: str = 'verification_uri'
GITHUB_KEY_INTERVAL:         str = 'interval'

GITHUB_API_HEADERS: dict[str, str] = {'Accept': 'application/json'}

DEVICE_CODE_URL: str = 'https://github.com/login/device/code'
TOKEN_URL:       str = 'https://github.com/login/oauth/access_token'


class PhaseOneResponse(TypedDict):
    device_code:      str
    user_code:        str
    verification_uri: str
    interval:         NotRequired[int]


class OAuthDeviceFlow:
    """
    Manages the GitHub OAuth Device Authorization Grant flow.

    This class encapsulates the API interactions required to authenticate a user 
    via a secondary device (e.g., a web browser). It implements the device flow 
    as a two-phase process:
    
    """
    def __init__(self, clientId: str) -> None:
        """

        Args:
            clientId (str): The unique GitHub Client ID for the OAuth Application.
        """

        if not clientId:
            raise RuntimeError('Error: clientId cannot be empty!')
        self._clientId:         str = clientId
        self._verificationData: GitHubAuthorizationData | None = None
        
    @property
    def userCode(self) -> str:
        if not self._verificationData:
            return ''
        return self._verificationData.userCode
        
    def executePhase1(self) -> None:
        """
        Requests the device and user codes from GitHub, extracts the
        verification payload, and launches the user's browser.
        """

        phaseOneResponse: PhaseOneResponse    = self._requestDeviceAndUserCodes(self._clientId)
        authData:     GitHubAuthorizationData = self._toGitHubAuthorizationData(phaseOneResponse)

        self._verificationData = authData
        webBrowserOpen(authData.verificationUrl)

    async def executePhase2(self) -> str:
        """
        Asynchronously polls the GitHub authorization server, handling
        'authorization_pending' and 'slow_down' backoff states until
        an access token is successfully generated.

        Raises:
        RuntimeError: If the provided clientId is empty, if the API fails to
                      return a device code, or if authentication is denied.

        """

        if not self._verificationData:
            raise RuntimeError('Phase 1 has not been executed.')
            
        tokenPayload: dict[str, str] = {
            'client_id':   self._clientId,
            'device_code': self._verificationData.deviceCode,
            'grant_type':  'urn:ietf:params:oauth:grant-type:device_code'
        }
        
        while True:
            tokenResponse: Response = post(TOKEN_URL, headers=GITHUB_API_HEADERS, data=tokenPayload)
            tokenData:     dict     = tokenResponse.json()
            
            if 'access_token' in tokenData:
                return tokenData['access_token']
                
            errorType: str = tokenData.get('error', '')
            if errorType == DF_AUTHORIZATION_PENDING:
                await sleep(self._verificationData.interval)
            elif errorType == DF_SLOW_DOWN:
                self._verificationData.interval += 5
                await sleep(self._verificationData.interval)
            else:
                raise RuntimeError(f'Authorization Failed: {errorType}')
                
    def _requestDeviceAndUserCodes(self, clientId: str) -> PhaseOneResponse:
        """

        Args:
            clientId:

        Returns:  The response JSON as a dictionary
        """

        payload:       dict[str, str] = {
            'client_id': clientId,
            'scope': 'repo'
        }
        
        response: Response = post(DEVICE_CODE_URL, headers=GITHUB_API_HEADERS, data=payload)
        return response.json()
        
    def _toGitHubAuthorizationData(self, phaseOneResponse: PhaseOneResponse) -> GitHubAuthorizationData:
        """
        Decodes the dictionary to a nice dataclass

        Args:
            phaseOneResponse:  The typed dictionary

        Returns:  The nice dataclass
        """
        #
        # mypy limitation: TypedDict.get() with variable keys evaluates to 'object' instead of the defined type
        #
        deviceCode:      str = phaseOneResponse.get(GITHUB_KEY_DEVICE_CODE, '')       # type: ignore
        userCode:        str = phaseOneResponse.get(GITHUB_KEY_USER_CODE, '')         # type: ignore
        verificationUrl: str = phaseOneResponse.get(GITHUB_KEY_VERIFICATION_URI, '')  # type: ignore
        interval:        int = phaseOneResponse.get(GITHUB_KEY_INTERVAL, 5)           # type: ignore

        if deviceCode == '' or deviceCode is None:
            raise RuntimeError('Failed to get device code.')
            
        return GitHubAuthorizationData(
            deviceCode=deviceCode,
            userCode=userCode,
            verificationUrl=verificationUrl,
            interval=interval
        )
