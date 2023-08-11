import sys
import warnings
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, cast

from packaging import version

from .. import model
from ..datapool import DataPool


F = TypeVar('F', bound=Callable[..., Any])


def ensure_access_token(invoke: Optional[bool] = False) -> Callable[[F], F]:
    """
    Decorator to ensure that a token is available.

    Args:
        func (callable): The function to be wrapped
        invoke (bool): Whether or not to invoke the function anyway.
    Returns:
        wrapper (callable): The decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(obj, *args, **kwargs):
            if isinstance(obj, BotMaestroSDKInterface):
                if obj.access_token is None:
                    if obj.RAISE_NOT_CONNECTED:
                        raise RuntimeError('Access Token not available. Make sure to invoke login first.')
                    else:
                        message = ""
                        if not obj._notified_disconnect:
                            obj._notified_disconnect = True
                            message += "** WARNING BotCity Maestro is not logged in and RAISE_NOT_CONNECTED is "
                            message += "False. Running on Offline mode. **"
                            warnings.warn(message, stacklevel=2)
                        message = f"Invoked '{func.__name__}'"
                        params: List[str] = []
                        if args:
                            for ar in args:
                                params.append(str(ar))
                        if kwargs:
                            for k, v in kwargs.items():
                                params.append(f"{k}={v}")
                        if params:
                            message += ' with arguments '
                            message += ", ".join(params)
                        message += "."
                        warnings.warn(message, stacklevel=2)
                        if not invoke:
                            return lambda *args, **kwargs: None
            else:
                raise NotImplementedError('ensure_token is only valid for BotMaestroSDK methods.')
            return func(obj, *args, **kwargs)

        return cast(F, wrapper)
    return decorator


def ensure_implementation() -> Callable[[F], F]:
    """
    Decorator to ensure that an implementation is available.

    Args:
        func (callable): The function to be wrapped
    Returns:
        wrapper (callable): The decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(obj, *args, **kwargs):
            if isinstance(obj, BotMaestroSDKInterface):
                if obj._impl is None:
                    obj._define_implementation()
            return func(obj, *args, **kwargs)

        return cast(F, wrapper)
    return decorator


def since_version(v: str) -> Callable[[F], F]:
    """
    Decorator to ensure that a method is availble for a given Maestro backend version.

    Args:
        func (callable): The function to be wrapped
        v (str): The minimum required version in the format X.Y.Z
    Returns:
        wrapper (callable): The decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(obj, *args, **kwargs):
            if isinstance(obj, BotMaestroSDKInterface):
                if obj.version is None:
                    if obj.RAISE_NOT_CONNECTED:
                        raise RuntimeError('Maestro version not available. Make sure to invoke login first.')
                else:
                    if version.parse(obj.version) < version.parse(v):
                        message = f'''
                        The method {func.__name__} is not available for your version of BotCity Maestro.
                        Your version: {obj.version} - Required version: {v}. Please request an update.
                        '''
                        raise RuntimeError(message)
            else:
                raise NotImplementedError('since_version is only valid for BotMaestroSDK methods.')
            return func(obj, *args, **kwargs)

        return cast(F, wrapper)
    return decorator


class BotMaestroSDKInterface:

    _notified_disconnect = False
    RAISE_NOT_CONNECTED = True
    # More details about VERIFY_SSL_CERT here
    # https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification
    VERIFY_SSL_CERT = True

    def __init__(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Main class to interact with the BotMaestro web portal.

        This class offers methods to send alerts, messages, create log entries, post artifacts and more.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        Attributes:
            access_token (str): The access token obtained via login.
        """
        self._server = None
        self._login = login
        self._key = key
        self._access_token = None
        self._task_id = 0
        self._impl: BotMaestroSDKInterface = None  # type: ignore
        self._version = None
        self.timeout = 30.0

        self.server = server

    @classmethod
    def from_sys_args(cls, default_server="", default_login="", default_key=""):
        if len(sys.argv) >= 4:
            maestro = cls()
            organization = ""
            try:
                server, task_id, token, organization, *_ = sys.argv[1:]
            except ValueError:
                server, task_id, token, *_ = sys.argv[1:]
            maestro.server = server
            maestro.access_token = token
            maestro.organization = organization
            maestro.task_id = task_id
        else:
            maestro = cls(
                server=default_server,
                login=default_login,
                key=default_key
            )
            if default_server:
                maestro.login()
        return maestro

    @property
    def server(self):
        """The server address"""
        return self._server

    @server.setter
    def server(self, server):
        # Remove additional end /
        if server and server[-1] == "/":
            server = server[:-1]
        self._server = server

    @property
    def access_token(self):
        """The access token"""
        return self._access_token

    @access_token.setter
    def access_token(self, token):
        self._access_token = token

    @property
    def organization(self):
        """The organization label"""
        return self._login

    @organization.setter
    def organization(self, organization):
        self._login = organization

    @property
    def task_id(self):
        """The Current Task ID"""
        return self._task_id

    @task_id.setter
    def task_id(self, task_id):
        self._task_id = task_id

    @property
    def version(self):
        """The BotCity Maestro Backend version"""
        return self._version

    def login(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Obtain an access token with the configured BotMaestro portal.

        Arguments are optional and can be used to configure or overwrite the object instantiation values.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        """
        raise NotImplementedError

    def logoff(self):
        """
        Revoke the access token used to communicate with the BotMaestro portal.
        """
        self.access_token = None
        self._impl = None  # type: ignore

    def alert(self, task_id: str, title: str, message: str, alert_type: model.AlertType) -> model.ServerMessage:
        """
        Register an alert message on the BotMaestro portal.

        Args:
            task_id: The activity label
            title: A title associated with the alert message
            message: The alert message
            alert_type: The alert type to be used. See [AlertType][botcity.maestro.model.AlertType]

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def message(self, email: List[str], users: List[str], subject: str, body: str,
                msg_type: model.MessageType, group: Optional[str] = None) -> model.ServerMessage:
        """
        Send an email message to the list of email and users given.

        Args:
            email: List of emails to receive the message.
            users: List of usernames registered on the BotMaestro portal to receive the message.
            subject: The message subject.
            body: The message body.
            msg_type: The message body type. See [MessageType][botcity.maestro.model.MessageType]
            group: The message group information.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def create_task(self, activity_label: str, parameters: Dict[str, object],
                    test: bool = False, *args, **kwargs) -> model.AutomationTask:
        """
        Creates a task to be executed on the BotMaestro portal.

        Args:
            activity_label: The activity unique identified.
            parameters: Dictionary with parameters and values for this task.
            test: Whether or not the task is a test.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        raise NotImplementedError

    def finish_task(self, task_id: str, status: model.AutomationTaskFinishStatus,
                    message: str = "") -> model.ServerMessage:
        """
        Finishes a given task.

        Args:
            task_id: The task unique identifier.
            status: The condition in which the task must be finished.
                See [AutomationTaskFinishStatus][botcity.maestro.model.AutomationTaskFinishStatus]
            message: A message to be associated with this action.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def restart_task(self, task_id: str) -> model.ServerMessage:
        """
        Restarts a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def get_task(self, task_id: str) -> model.AutomationTask:
        """
        Return details about a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        raise NotImplementedError

    def interrupt_task(self, task_id: str) -> model.ServerMessage:
        """
        Request the interruption of a given task.

        Args:
            task_id (str): The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def new_log(self, activity_label: str, columns: List[model.Column]) -> model.ServerMessage:
        """
        Create a new log on the BotMaestro portal.

        Args:
            activity_label: The activity unique identifier.
            columns: A list of [Columns][botcity.maestro.model.Column]

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def new_log_entry(self, activity_label: str, values: Dict[str, object]) -> model.ServerMessage:
        """
        Creates a new log entry.

        Args:
            activity_label: The activity unique identifier.
            values: Dictionary in which the key is the column label and value is the entry value.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def get_log(self, activity_label: str, date: Optional[str] = "") -> List[Dict[str, object]]:
        """
        Fetch log information.

        Args:
            activity_label: The activity unique identifier.
            date: Initial date for log information in the format DD/MM/YYYY. If empty all information is retrieved.

        Returns:
            Log entry list. Each element in the list is a dictionary in which keys are Column names and values are
            the column value.
        """
        raise NotImplementedError

    def delete_log(self, activity_label: str) -> model.ServerMessage:
        """
        Fetch log information.

        Args:
            activity_label: The activity unique identifier.

        Returns:
            Log entry list. Each element in the list is a dictionary in which keys are Column names and values are
            the column value.
        """
        raise NotImplementedError

    def post_artifact(self, task_id: int, artifact_name: str, filepath: str) -> model.ServerMessage:
        """
        Upload a new artifact into the BotMaestro portal.

        Args:
            task_id: The task unique identifier.
            artifact_name: The name of the artifact to be displayed on the portal.
            filepath: The file to be uploaded.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        raise NotImplementedError

    def list_artifacts(self) -> List[model.Artifact]:
        """
        List all artifacts available for the organization.

        Returns:
            List of artifacts. See [Artifact][botcity.maestro.model.Artifact]
        """
        raise NotImplementedError

    def get_artifact(self, artifact_id: int) -> Tuple[str, bytes]:
        """
        Retrieve an artifact from the BotMaestro portal.

        Args:
            artifact_id: The artifact unique identifier.

        Returns:
            Tuple containing the artifact name and an array of bytes which are the binary content of the artifact.
        """
        raise NotImplementedError

    @ensure_access_token(invoke=True)
    def get_execution(self, task_id: Optional[str] = None) -> model.BotExecution:
        """
        Fetch the BotExecution object for a given task.

        Args:
            task_id (Optional[str], optional): The task ID. Defaults to None.

        Returns:
            model.BotExecution: The BotExecution information.
        """
        task_id = task_id or self.task_id

        if not self.access_token and not self.RAISE_NOT_CONNECTED:
            return model.BotExecution("", task_id, "", {})

        if not task_id:
            # If we are connected (access_token) or want to raise errors when disconnected
            # we show the error, otherwise we are working offline and just want to ignore this
            # but we will print a warning message for good measure
            raise ValueError("A task ID must be informed either via the parameter or the class property.")

        parameters = self.get_task(task_id).parameters

        execution = model.BotExecution(self.server, task_id, self.access_token, parameters)
        return execution

    def error(self, task_id: int, exception: Exception, screenshot: Optional[str] = None,
              attachments: Optional[List[str]] = None, tags: Optional[Dict[str, str]] = None):
        """Create a new Error entry.

        Args:
            task_id (int): The task unique identifier.
            exception (Exception): The exception object.
            screenshot (Optional[str], optional): File path for a screenshot to be attached
                to the error. Defaults to None.
            attachments (Optional[List[str]], optional): Additional files to be sent along
                with the error entry. Defaults to None.
            tags (Optional[Dict[str, str]], optional): Dictionary with tags to be associated
                with the error entry. Defaults to None.

        Raises:
            ValueError: If the request fails, a ValueError exception is raised.
        """
        raise NotImplementedError

    def create_credential(self, label: str, key: str, value: str):
        """Create a new key/value entry for a credentials set.

        Args:
            label (str): The credential set label
            key (str): The key identifier for this credential
            value (str): The value associated with this key

        """
        raise NotImplementedError

    def get_credential(self, label: str, key: str) -> str:
        """
        Get value in key inside credentials
        Args:
            label: Credential set name
            key: Key name within the credential set

        Returns:
            value (str): Key value that was requested
        """
        raise NotImplementedError

    def create_datapool(self, pool) -> DataPool:
        """
        Create a new datapool on the BotMaestro portal.

        Args:
            pool: The DataPool [DataPool][botcity.maestro.datapool.DataPool] instance.

        Returns:
            DataPool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool] instance.
        """
        raise NotImplementedError

    def get_datapool(self, label: str) -> DataPool:
        """
        Get datapool on the BotMaestro portal.

        Args:
            label: Label DataPool.

        Returns:
            DataPool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool] instance.
        """
        raise NotImplementedError
