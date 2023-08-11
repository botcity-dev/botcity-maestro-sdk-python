from typing import Dict, List, Optional, Tuple

import requests
import urllib3

from . import model
from .impl import (BotMaestroSDKInterface, v1, v2,
                   ensure_access_token, ensure_implementation, since_version)

from .datapool import DataPool

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BotMaestroSDK(BotMaestroSDKInterface):

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
        super().__init__(server=server, login=login, key=key)

    def _define_implementation(self):
        try:
            url = f'{self._server}/api/v2/maestro/version'

            with requests.get(url, verify=self.VERIFY_SSL_CERT) as req:
                try:
                    if req.status_code == 200:
                        self._impl = v2.BotMaestroSDKV2(self.server, self._login, self._key, sdk=self)
                        self._version = req.json()['version']
                finally:
                    if self._impl is None:
                        self._impl = v1.BotMaestroSDKV1(self.server, self._login, self._key, sdk=self)
                        self._version = "1.0.0"
            self._impl.access_token = self.access_token
            self._impl._login = self._login
        except Exception as ex:
            if self.RAISE_NOT_CONNECTED:
                raise ex
            self._impl = v2.BotMaestroSDKV2(self.server, self._login, self._key, sdk=self)
            self._version = "999.0.0"
            self._impl.access_token = self.access_token
            self._impl._login = self._login

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
        self._impl.login()
        self.access_token = self._impl.access_token

    @ensure_implementation()
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
        return self._impl.alert(task_id=task_id, title=title, message=message, alert_type=alert_type)

    @ensure_implementation()
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
        return self._impl.message(email=email, users=users, subject=subject, body=body, msg_type=msg_type,
                                  group=group)

    @ensure_implementation()
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

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        return self._impl.create_task(activity_label=activity_label, parameters=parameters, test=test,
                                      min_execution_date=min_execution_date, priority=priority)

    @ensure_implementation()
    @ensure_access_token()
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
        return self._impl.finish_task(task_id=task_id, status=status, message=message)

    @ensure_implementation()
    @ensure_access_token()
    def restart_task(self, task_id: str) -> model.ServerMessage:
        """
        Restarts a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        return self._impl.restart_task(task_id=task_id)

    @ensure_implementation()
    @ensure_access_token()
    def get_task(self, task_id: str) -> model.AutomationTask:
        """
        Return details about a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        return self._impl.get_task(task_id=task_id)

    @ensure_implementation()
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
        return self._impl.interrupt_task(task_id=task_id)

    @ensure_implementation()
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
        return self._impl.new_log(activity_label=activity_label, columns=columns)

    @ensure_implementation()
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
        return self._impl.new_log_entry(activity_label=activity_label, values=values)

    @ensure_implementation()
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
        return self._impl.get_log(activity_label=activity_label, date=date)

    @ensure_implementation()
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
        return self._impl.delete_log(activity_label=activity_label)

    @ensure_implementation()
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
        return self._impl.post_artifact(task_id=task_id, artifact_name=artifact_name, filepath=filepath)

    @ensure_implementation()
    @ensure_access_token()
    def list_artifacts(self) -> List[model.Artifact]:
        """
        List all artifacts available for the organization.

        Returns:
            List of artifacts. See [Artifact][botcity.maestro.model.Artifact]
        """
        return self._impl.list_artifacts()

    @ensure_implementation()
    @ensure_access_token()
    def get_artifact(self, artifact_id: int) -> Tuple[str, bytes]:
        """
        Retrieve an artifact from the BotMaestro portal.

        Args:
            artifact_id: The artifact unique identifier.

        Returns:
            Tuple containing the artifact name and an array of bytes which are the binary content of the artifact.
        """
        return self._impl.get_artifact(artifact_id=artifact_id)

    @ensure_implementation()
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
        return self._impl.error(task_id, exception, screenshot, attachments, tags)

    @ensure_implementation()
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
        return self._impl.get_credential(label, key)

    @ensure_implementation()
    @since_version("2.0.0")
    @ensure_access_token()
    def create_credential(self, label: str, key: str, value):
        """
        Create credential
        Args:
            label: Credential set name
            key: Key name within the credential set
            value: Credential value
        """
        return self._impl.create_credential(label, key, value)

    @ensure_implementation()
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
        new_pool = self._impl.create_datapool(pool=pool)
        return new_pool

    @ensure_implementation()
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
        pool = self._impl.get_datapool(label=label)
        return pool
