
from asyncio import sleep

from requests import Response
from requests import post

from webbrowser import open as webBrowserOpen

from githubauth.GitHubAuthorizationData import GitHubAuthorizationData


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
            clientId (str): The unique GitHub Client ID for the OAuth Application.:
        """

        if not clientId:
            raise RuntimeError('Error: clientId cannot be empty!')
        self._clientId: str = clientId
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

        responseDict: dict                    = self._requestDeviceAndUserCodes(self._clientId)
        authData:     GitHubAuthorizationData = self._toGitHubAuthorizationData(responseDict)

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
            
        tokenUrl: str            = 'https://github.com/login/oauth/access_token'
        headers:  dict[str, str] = {'Accept': 'application/json'}

        tokenPayload: dict[str, str] = {
            'client_id':   self._clientId,
            'device_code': self._verificationData.deviceCode,
            'grant_type':  'urn:ietf:params:oauth:grant-type:device_code'
        }
        
        while True:
            tokenResponse: Response = post(tokenUrl, headers=headers, data=tokenPayload)
            tokenData:     dict     = tokenResponse.json()
            
            if 'access_token' in tokenData:
                return tokenData['access_token']
                
            errorType: str = tokenData.get('error', '')
            if errorType == 'authorization_pending':
                await sleep(self._verificationData.interval)
            elif errorType == 'slow_down':
                self._verificationData.interval += 5
                await sleep(self._verificationData.interval)
            else:
                raise RuntimeError(f'Auth Failed: {errorType}')
                
    def _requestDeviceAndUserCodes(self, clientId: str) -> dict:

        deviceCodeUrl: str            = 'https://github.com/login/device/code'
        headers:       dict[str, str] = {'Accept': 'application/json'}
        payload:       dict[str, str] = {
            'client_id': clientId,
            'scope': 'repo'
        }
        
        response: Response = post(deviceCodeUrl, headers=headers, data=payload)
        return response.json()
        
    def _toGitHubAuthorizationData(self, responseDict: dict) -> GitHubAuthorizationData:

        deviceCode:      str = responseDict.get('device_code', '')
        userCode:        str = responseDict.get('user_code', '')
        verificationUrl: str = responseDict.get('verification_uri', '')
        interval:        int = responseDict.get('interval', 5)
        
        if not deviceCode:
            raise RuntimeError('Failed to get device code.')
            
        return GitHubAuthorizationData(
            deviceCode=deviceCode,
            userCode=userCode,
            verificationUrl=verificationUrl,
            interval=interval
        )
