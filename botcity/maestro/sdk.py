import datetime
import json
import os
import platform
import sys
import traceback
import warnings
from dataclasses import asdict
from functools import wraps
from io import IOBase, StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, cast

import distro
import importlib_metadata
import requests
import urllib3
from packaging import version
from requests_toolbelt import MultipartEncoder

from . import model
from .datapool import DataPool

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


F = TypeVar('F', bound=Callable[..., Any])


def _get_return_type(func: F) -> Any:
    return func.__annotations__.get('return', None)


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
            if isinstance(obj, BotMaestroSDK):
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
                            if obj.MOCK_OBJECT_WHEN_DISCONNECTED:
                                # We need to return an object of the same type as the function
                                # so we get the return type and return an empty object of that type
                                try:
                                    return _get_return_type(func)()
                                except Exception:
                                    # If we can't get the return type or fail to create one, return None
                                    return None
                            return lambda *args, **kwargs: None
            else:
                raise NotImplementedError('ensure_token is only valid for BotMaestroSDK methods.')
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
            if isinstance(obj, BotMaestroSDK):
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


class BotMaestroSDK:
    _notified_disconnect = False
    RAISE_NOT_CONNECTED = True
    # More details about VERIFY_SSL_CERT here
    # https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification
    VERIFY_SSL_CERT = True
    MOCK_OBJECT_WHEN_DISCONNECTED = False

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
        self._version = None
        self._timeout = 30.0

        self.server = server

    def _define_implementation(self):
        try:
            url = f'{self._server}/api/v2/maestro/version'

            with requests.get(url, verify=self.VERIFY_SSL_CERT, timeout=self._timeout) as req:
                req.raise_for_status()
                self._version = req.json()['version']
        except Exception as ex:
            if self.RAISE_NOT_CONNECTED:
                raise ex
            self._version = "999.0.0"

    def _headers(self) -> Dict:
        """The HTTP header for BotCity Maestro communication"""
        return {
            "Content-Type": "application/json",
            "token": self.access_token,
            "organization": self.organization
        }

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
            maestro._define_implementation()
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

    @property
    def timeout(self):
        """The timeout for the requests"""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def is_online(self):
        """Whether or not the object is connected to the BotCity Orchestrator portal"""
        return self.access_token is not None and self.access_token != ""

    def login(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Obtain an access token with the configured BotMaestro portal.

        Arguments are optional and can be used to configure or overwrite the object instantiation values.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        """
        if server:
            self.server = server
        self._login = login or self._login
        self._key = key or self._key
        if not self._server:
            raise ValueError('Server is required.')
        if not self._login:
            raise ValueError('Login is required.')
        if not self._key:
            raise ValueError('Key is required.')
        self.logoff()

        self._define_implementation()
        url = f'{self._server}/api/v2/workspace/login'
        data = {"login": self.organization, "key": self._key}
        headers = {'Content-Type': 'application/json'}

        with requests.post(
            url, data=json.dumps(data), headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                self.access_token = req.json()['accessToken']
            else:
                raise ValueError('Error during login. Server returned %d. %s' % (req.status_code, req.text))

    def logoff(self):
        """
        Revoke the access token used to communicate with the BotMaestro portal.
        """
        self.access_token = None

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

    @ensure_access_token()
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
        url = f'{self._server}/api/v2/alerts'

        data = {"taskId": task_id, "title": title,
                "message": message, "type": alert_type}

        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:

                raise ValueError('Error during alert. %s', req.text)

    @ensure_access_token()
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
        url = f'{self._server}/api/v2/message'

        if not group:
            group = ""

        data = {"emails": email, "logins": users, "subject": subject, "body": body,
                "type": msg_type, "group": group}
        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )
            payload = json.dumps({"message": req.text, "type": req.status_code})
            return model.ServerMessage.from_json(payload=payload)

    @ensure_access_token()
    def create_task(self, activity_label: str, parameters: Dict[str, object],
                    test: bool = False, priority: int = 0, min_execution_date=None) -> model.AutomationTask:
        """
        Creates a task to be executed on the BotMaestro portal.

        Args:
            activity_label: The activity unique identified.
            parameters: Dictionary with parameters and values for this task.
            test: Whether or not the task is a test.
            priority: (Optional[int], optional) An integer from 0 to 10 to refer to execution priority.
            min_execution_date (Optional[datetime.datetime], optional): Minimum execution date for the task.

        Warning:
            The BotCity Orchestrator time zone is in UTC-0. Therefore, consider the difference between
            time zones when using the `min_execution_date` parameter.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        url = f'{self._server}/api/v2/task'

        data = {
            "activityLabel": activity_label, "test": test, "parameters": parameters, "priority": priority,
        }

        if min_execution_date is not None:
            if not isinstance(min_execution_date, datetime.datetime):
                raise ValueError(f"Arg 'min_execution_date' is not datetime. Type {type(min_execution_date)}")
            data["minExecutionDate"] = min_execution_date.isoformat()

        headers = self._headers()
        with requests.post(
            url, json=data, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.AutomationTask.from_json(req.text)
            else:
                try:
                    message = 'Error during task create. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task create. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @staticmethod
    def _validate_items(total_items, processed_items, failed_items):
        if total_items == processed_items == failed_items is None:
            # If all are None, return None for all
            msg = """
Attention: this task is not reporting items. Please inform the total, processed and failed items.
Reporting items is a crucial step to calculate the ROI, success rate and other metrics for your automation
via BotCity Insights.
            """
            warnings.warn(msg, stacklevel=4)
            return None, None, None
        if total_items is None and processed_items is not None and failed_items is not None:
            # If total is None, but processed and failed are not, then total is the sum of both
            total_items = processed_items + failed_items
        if total_items is not None and processed_items is not None and failed_items is None:
            # If total and processed are not None, but failed is, then failed is the difference
            failed_items = total_items - processed_items
        if total_items is not None and processed_items is None and failed_items is not None:
            # If total and failed are not None, but processed is, then processed is the difference
            processed_items = total_items - failed_items

        if total_items is None or processed_items is None or failed_items is None:
            raise ValueError(
                "You must inform at least two of the following parameters: total_items, processed_items, failed_items."
            )

        # Make sure no negative values are present
        total_items = max(0, total_items)
        processed_items = max(0, processed_items)
        failed_items = max(0, failed_items)
        if total_items is not None and processed_items is not None and failed_items is not None:
            if total_items != processed_items + failed_items:
                raise ValueError("Total items is not equal to the sum of processed and failed items.")
        return total_items, processed_items, failed_items

    @ensure_access_token()
    def finish_task(self, task_id: str, status: model.AutomationTaskFinishStatus,
                    message: str = "", total_items: int = None, processed_items: int = None,
                    failed_items: int = None) -> model.ServerMessage:
        """
        Finishes a given task.

        Args:
            task_id: The task unique identifier.
            status: The condition in which the task must be finished.
                See [AutomationTaskFinishStatus][botcity.maestro.model.AutomationTaskFinishStatus]
            message: A message to be associated with this action.
            total_items: Total number of items processed by the task.
            processed_items: Number items processed successfully by the task.
            failed_items: Number items failed to be processed by the task.

        Note:
            Starting from version 0.5.0, the parameters `total_items`, `processed_items` and `failed_items` are
            available to be used. It is important to report the correct values for these parameters as they are used
            to calculate the ROI, success rate and other metrics.

            Keep in mind that the sum of `processed_items` and `failed_items` must be equal to `total_items`. If
            `total_items` is None, then the sum of `processed_items` and `failed_items` will be used as `total_items`.
            If you inform `total_items` and `processed_items`, then `failed_items` will be calculated as the difference.


        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/task/{task_id}'

        total_items, processed_items, failed_items = self._validate_items(total_items, processed_items, failed_items)

        data = {"finishStatus": status, "finishMessage": message,
                "state": "FINISHED", "totalItems": total_items,
                "processedItems": processed_items, "failedItems": failed_items}

        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task finish. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task finish. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def restart_task(self, task_id: str) -> model.ServerMessage:
        """
        Restarts a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/task/{task_id}'
        data = {"state": "START"}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task restart. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task restart. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def get_task(self, task_id: str) -> model.AutomationTask:
        """
        Return details about a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        url = f'{self._server}/api/v2/task/{task_id}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                payload = req.text
                return model.AutomationTask.from_json(payload)
            else:
                try:
                    message = 'Error during task get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @since_version("2.0.0")
    @ensure_access_token()
    def interrupt_task(self, task_id: str) -> model.ServerMessage:
        """
        Request the interruption of a given task.

        Args:
            task_id (str): The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/task/{task_id}'
        data = {"interrupted": True}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task finish. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task finish. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def new_log(self, activity_label: str, columns: List[model.Column]) -> model.ServerMessage:
        """
        Create a new log on the BotMaestro portal.

        Args:
            activity_label: The activity unique identifier.
            columns: A list of [Columns][botcity.maestro.model.Column]

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/log'

        cols = [asdict(c) for c in columns]

        data = {"activityLabel": activity_label, "columns": cols, 'organizationLabel': self.organization}
        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during new log. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def new_log_entry(self, activity_label: str, values: Dict[str, object]) -> model.ServerMessage:
        """
        Creates a new log entry.

        Args:
            activity_label: The activity unique identifier.
            values: Dictionary in which the key is the column label and value is the entry value.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/log/{activity_label}/entry'

        with requests.post(
            url, json=values, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type": req.status_code})
            return model.ServerMessage.from_json(payload=payload)

    @ensure_access_token()
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
        url = f'{self._server}/api/v2/log/{activity_label}'

        days = 365  # 1 year is enough
        if date:
            days = (datetime.datetime.now()-datetime.datetime.strptime(date, "%d/%m/%Y")).days + 1

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                log = req.json()
                columns = log.get('columns')
                if not columns:
                    raise ValueError('Malformed log. No columns available.')
                names_for_labels = {c['label']: c['name'] for c in columns}
                url = f'{self._server}/api/v2/log/{activity_label}/entry-list'

                data = {"days": days}
                with requests.get(
                    url, params=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
                ) as entry_req:
                    if entry_req.ok:
                        log_data = []
                        for en in entry_req.json():
                            cols = en['columns']
                            d = dict()
                            for label, name in names_for_labels.items():
                                d[name] = cols[label]
                            log_data.append(d)
                        return log_data
                    else:
                        try:
                            message = 'Error during log entry read. Server returned %d. %s' % (
                                entry_req.status_code, entry_req.json().get('message', ''))
                        except ValueError:
                            message = 'Error during log entry read. Server returned %d. %s' % (
                                entry_req.status_code, entry_req.text)
                        raise ValueError(message)
            else:
                try:
                    message = 'Error during log read. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log read. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def delete_log(self, activity_label: str) -> model.ServerMessage:
        """
        Fetch log information.

        Args:
            activity_label: The activity unique identifier.

        Returns:
            Log entry list. Each element in the list is a dictionary in which keys are Column names and values are
            the column value.
        """
        # date  a partir desta data
        # date em branco eh tudo
        url = f'{self._server}/api/v2/log/{activity_label}'

        with requests.delete(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during log delete. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log delete. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type": req.status_code})
            return model.ServerMessage.from_json(payload=payload)

    @ensure_access_token()
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
        file = Path(filepath)

        if not file.exists():
            raise FileNotFoundError(f"No such file: {filepath}")

        if not file.is_file():
            raise ValueError("Invalid file type. Please make sure you are using a valid file path "
                             "and not pointing to a directory.")

        file_extension = file.suffix
        if not artifact_name.endswith(file_extension):
            artifact_name = f"{artifact_name}{file_extension}"

        artifact_id = self._create_artifact(task_id=task_id, name=artifact_name, filename=artifact_name)
        url = f'{self._server}/api/v2/artifact/log/{json.loads(artifact_id.payload)["id"]}'

        with open(filepath, 'rb') as f:
            data = MultipartEncoder(
                fields={'file': (artifact_name, f)}
            )
            headers = {**self._headers(), 'Content-Type': data.content_type}
            with requests.post(
                url, data=data, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT
            ) as req:
                if req.ok:
                    return artifact_id
                else:
                    try:
                        message = 'Error during artifact posting. Server returned %d. %s' % (
                            req.status_code, req.json().get('message', ''))
                    except ValueError:
                        message = 'Error during artifact posting. Server returned %d. %s' % (
                            req.status_code, req.text)
                    raise ValueError(message)

    @ensure_access_token()
    def _create_artifact(self, task_id: int, name: str, filename: str) -> model.ServerMessage:
        """
        Creates a new artifact

        Args:
            task_id: The task unique identifier.
            name: The name of the artifact to be displayed on the portal.
            filename: The file to be uploaded.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/artifact'
        data = {'taskId': task_id, 'name': name, 'filename': filename}
        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def list_artifacts(self, days: int = 7) -> List[model.Artifact]:
        """
        List all artifacts available for the organization.

        Returns:
            List of artifacts. See [Artifact][botcity.maestro.model.Artifact]
        """
        url = f'{self._server}/api/v2/artifact?size=5&page=0&sort=dateCreation,desc&days={days}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                content = req.json()['content']
                response = [model.Artifact.from_dict(a) for a in content]
                for page in range(1, req.json()['totalPages']):
                    url = f'{self._server}/api/v2/artifact?size=5&page={page}&sort=dateCreation,desc&days={days}'
                    with requests.get(
                        url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
                    ) as req:
                        content = req.json()['content']
                        response.extend([model.Artifact.from_dict(a) for a in content])
                return response
            else:
                try:
                    message = 'Error during artifact listing. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact listing. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @ensure_access_token()
    def get_artifact(self, artifact_id: int) -> Tuple[str, bytes]:
        """
        Retrieve an artifact from the BotMaestro portal.

        Args:
            artifact_id: The artifact unique identifier.

        Returns:
            Tuple containing the artifact name and an array of bytes which are the binary content of the artifact.
        """
        url = f'{self._server}/api/v2/artifact/{artifact_id}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                payload = req.json()
                filename = payload['fileName']

                url = f'{self.server}/api/v2/artifact/{artifact_id}/file'
                with requests.get(
                    url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
                ) as req_file:
                    file_content = req_file.content

                return filename, file_content
            else:
                try:
                    message = 'Error during artifact get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @since_version("2.0.0")
    @ensure_access_token()
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
        url = f'{self._server}/api/v2/error'
        trace = " ".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

        if not tags:
            tags = dict()

        default_tags = self._get_default_error_tags()
        default_tags.update(tags)
        tags = default_tags

        data = {'taskId': task_id, 'type': exception.__class__.__name__, 'message': str(exception),
                'stackTrace': trace, 'language': 'PYTHON', 'tags': tags}

        response = None
        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.status_code == 201:
                response = req.json()
            else:
                try:
                    message = 'Error during new error entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new error entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

        if screenshot:
            self._create_screenshot(error_id=response.get('id'), filepath=screenshot)

        # pip list
        packages = [(dist.name.lower(), dist.version) for dist in importlib_metadata.distributions()]
        packages.sort(key=lambda x: x[0])  # type: ignore
        buffer = StringIO()
        buffer.writelines([f"{name}=={version}{os.linesep}" for name, version in packages])
        buffer.flush()
        self._create_attachment(
            error_id=response.get('id'),
            filename="piplist.txt",
            buffer=buffer
        )
        buffer.close()

        if attachments:
            for attachment in attachments:
                filepath = os.path.expandvars(os.path.expanduser(attachment))
                with open(filepath, 'rb') as f:
                    self._create_attachment(
                        error_id=response.get('id'),
                        filename=Path(filepath).name,
                        buffer=f
                    )

        return response

    def _get_default_error_tags(self) -> Dict:
        """Generates a dictionarty with useful tags about the system for the error method
        """
        tags = dict()
        try:
            tags["user_name"] = os.getlogin()
        except Exception:
            tags["user_name"] = ""
        tags["host_name"] = platform.node()
        tags["os_name"] = platform.system()

        os_version = platform.version()
        if platform.system() == "Linux":
            os_version = " ".join(distro.linux_distribution())
        elif platform.system() == "Darwin":
            os_version = platform.mac_ver()[0]

        tags["os_version"] = os_version
        tags["python_version"] = platform.python_version()

        return tags

    def _create_screenshot(self, error_id: int, filepath: str) -> None:
        """
        Creates a new screenshot in error

        Args:
            error_id: The error unique identifier.
            filepath: File path for screenshot
        Returns:
            None
        """
        url_screenshot = f'{self._server}/api/v2/error/{error_id}/screenshot'
        filepath = os.path.expandvars(os.path.expanduser(filepath))

        with open(filepath, 'rb') as f:
            data_screenshot = MultipartEncoder(
                fields={'file': (Path(filepath).name, f)}
            )
            headers = self._headers()
            headers['Content-Type'] = data_screenshot.content_type

            with requests.post(
                url_screenshot, data=data_screenshot, headers=headers,
                timeout=self._timeout, verify=self.VERIFY_SSL_CERT
            ) as req:
                if not req.ok:
                    try:
                        message = 'Error during new log entry. Server returned %d. %s' % (
                            req.status_code, req.json().get('message', ''))
                    except ValueError:
                        message = 'Error during new log entry. Server returned %d. %s' % (
                            req.status_code, req.text)
                    raise ValueError(message)

    def _create_attachment(self, error_id: int, filename: str, buffer: IOBase):
        """
        Creates a new attachment in error

        Args:
            error_id (int): The error unique identifier.
            filename (str): The file name to be displayed.
            buffer (IOBase): The file handler buffer.
        """
        url_attachments = f'{self._server}/api/v2/error/{error_id}/attachments'

        file = MultipartEncoder(
            fields={'file': (filename, buffer)}
        )
        headers = self._headers()
        headers['Content-Type'] = file.content_type
        with requests.post(
            url_attachments, data=file, headers=headers, timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if not req.ok:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.text)
                raise ValueError(message)

    @since_version("2.0.0")
    @ensure_access_token()
    def get_credential(self, label: str, key: str) -> str:
        """
        Get value in key inside credentials
        Args:
            label: Credential set name
            key: Key name within the credential set

        Returns:
            Key value that was requested
        """
        url = f'{self._server}/api/v2/credential/{label}/key/{key}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return str(req.text)
            else:
                try:
                    message = 'Error during log read. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log read. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    @since_version("2.0.0")
    @ensure_access_token()
    def create_credential(self, label: str, key: str, value):
        """
        Create credential in a credentials set
        Args:
            label: Credential set name
            key: Key name within the credential set
            value: Credential value
        """
        credential = self._get_credential_by_label(label=label)

        if credential is None:
            secrets = [
                {'key': key, 'value': value, 'valid': True}
            ]
            response = self._create_credential_by_label(label=label, secrets=secrets)
            if response is None:
                raise ValueError('Error during create credential.')
            return response.to_json()
        data = {
            'key': key,
            'value': value
        }
        url = f'{self._server}/api/v2/credential/{label}/key'
        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if not req.ok:
                req.raise_for_status()

    @since_version("3.0.0")
    @ensure_access_token()
    def update_credential(self, label: str, key: str, new_value):
        """Update a credential with a new value
        Args:
            label: Credential set name
            key: Key name within the credential set
            new_value: Credential new value
        """
        credential = self._get_credential_by_label(label=label, raise_exception=True)
        secrets = credential.get("secrets", [])
        index = self._get_secrets_key_index(label=label, key=key, secrets=secrets)
        secrets[index]['value'] = new_value
        self._edit_credential_by_label(label, secrets=secrets)

    @since_version("3.0.0")
    @ensure_access_token()
    def remove_credential(self, label: str, key: str):
        """Removes a credential from the set
        Args:
            label: Credential set name
            key: Key name within the credential set
        """
        credential = self._get_credential_by_label(label=label, raise_exception=True)
        secrets = credential.get("secrets", [])
        index = self._get_secrets_key_index(label=label, key=key, secrets=secrets)
        del secrets[index]
        self._edit_credential_by_label(label, secrets=secrets)

    def _get_secrets_key_index(self, label: str, key: str, secrets: list):
        """
        Find and return the index of a given key in the secrets list.
        Args:
            label: Credential set name
            key: Key name within the credential set
            secrets: List of secret dictionary entries
        Returns:
            The key index or None in case it is not found
        """
        index = next((i for i, d in enumerate(secrets) if d.get('key') == key), None)
        if index is None:
            raise ValueError(f"Key '{key}' does not exist in credential set '{label}'.")
        return index

    def _get_credential_by_label(self, label, raise_exception: bool = False):
        """
        Get dict in key inside credentials
        Args:
            label: Credential set name
            raise_exception: Whether or not to raise exception in case the credential set is not found
        Returns:
            Credential dict
        """
        url = f'{self._server}/api/v2/credential/{label}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return json.loads(model.ServerMessage.from_json(req.text).payload)
            else:
                if raise_exception:
                    req.raise_for_status()
                return None

    def _create_credential_by_label(self, label: str, secrets: list):
        data = {
            'label': label,
            'secrets': secrets
        }
        url = f'{self._server}/api/v2/credential'

        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            req.raise_for_status()

    def _edit_credential_by_label(self, label: str, secrets: list):
        data = {
            'label': label,
            'secrets': secrets
        }
        url = f'{self._server}/api/v2/credential/{label}'

        with requests.post(
            url, json=data, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT
        ) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            req.raise_for_status()

    @since_version("3.0.2")
    @ensure_access_token()
    def create_datapool(self, pool) -> DataPool:
        """
        Create a new datapool on the BotMaestro portal.

        Args:
            pool: The DataPool [DataPool][botcity.maestro.datapool.DataPool] instance.

        Returns:
            DataPool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool] instance.
        """
        url = f'{self.server}/api/v2/datapool'
        pool.maestro = self
        with requests.post(url, data=json.dumps(pool.to_dict()), headers=self._headers(),
                           timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return pool
            req.raise_for_status()

    @since_version("3.0.2")
    @ensure_access_token()
    def get_datapool(self, label: str) -> DataPool:
        """
        Get datapool on the BotMaestro portal.

        Args:
            label: Label DataPool.

        Returns:
            DataPool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool] instance.
        """
        url = f'{self._server}/api/v2/datapool/{label}'

        with requests.get(url, headers=self._headers(), timeout=self._timeout, verify=self.VERIFY_SSL_CERT) as req:
            if req.ok:
                return DataPool.from_json(payload=req.content, maestro=self)
            req.raise_for_status()
