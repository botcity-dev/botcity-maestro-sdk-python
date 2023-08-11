import json
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

import requests

from .. import model
from .interface import BotMaestroSDKInterface, ensure_access_token


class BotMaestroSDKV1(BotMaestroSDKInterface):

    def __init__(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None,
                 sdk: Optional[BotMaestroSDKInterface] = None):
        """
        Main class to interact with the BotMaestro web portal.

        This class offers methods to send alerts, messages, create log entries, post artifacts and more.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`
            sdk: The BotMaestroSDK instance

        Attributes:
            access_token (str): The access token obtained via login.
        """
        super().__init__(server=server, login=login, key=key)
        self._sdk: BotMaestroSDKInterface = sdk  # type: ignore

    def login(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Obtain an access token with the configured BotMaestro portal.

        Arguments are optional and can be used to configure or overwrite the object instantiation values.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        """
        url = f'{self._sdk._server}/app/api/login'
        data = {"userLogin": self._sdk._login, "key": self._sdk._key}

        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                self.access_token = req.json()['access_token']
            else:
                raise ValueError('Error during login. Server returned %d. %s' % (req.status_code, req.text))

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
        url = f'{self._sdk._server}/app/api/alert/send'

        data = {"taskId": task_id, "title": title,
                "message": message, "type": alert_type,
                "access_token": self.access_token
                }

        with requests.post(url, data=data) as req:
            if req.status_code == 200:
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
        url = f'{self._sdk._server}/app/api/message/send'

        if not group:
            group = ""

        email_str = ",".join(email)
        users_str = ",".join(users)

        data = {"email": email_str, "users": users_str, "subject": subject, "body": body,
                "type": msg_type, "group": group, "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )

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
        url = f'{self._sdk._server}/app/api/task/create'

        data = {
            "activityLabel": activity_label, "taskForTest": str(test).lower(), "access_token": self.access_token
        }
        data.update(parameters)

        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                payload = req.json().get('payload')
                return model.AutomationTask.from_json(payload)
            else:
                try:
                    message = 'Error during task create. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task create. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

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
        url = f'{self._sdk._server}/app/api/task/finish'

        processed_items = "1"  # TODO: Check this constant value here.

        data = {"taskId": task_id, "finishStatus": status, "finishMessage": message,
                "processedItems": processed_items, "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task finish. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task finish. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def restart_task(self, task_id: str) -> model.ServerMessage:
        """
        Restarts a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._sdk._server}/app/api/task/restart'

        data = {"id": task_id, "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task restart. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task restart. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def get_task(self, task_id: str) -> model.AutomationTask:
        """
        Return details about a given task.

        Args:
            task_id: The task unique identifier.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        url = f'{self._sdk._server}/app/api/task/get'

        data = {"id": task_id, "access_token": self.access_token}
        with requests.get(url, params=data) as req:
            if req.status_code == 200:
                payload = req.text
                return model.AutomationTask.from_json(payload)
            else:
                try:
                    message = 'Error during task get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def new_log(self, activity_label: str, columns: List[model.Column]) -> model.ServerMessage:
        """
        Create a new log on the BotMaestro portal.

        Args:
            activity_label: The activity unique identifier.
            columns: A list of [Columns][botcity.maestro.model.Column]

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._sdk._server}/app/api/log/create'

        cols = [asdict(c) for c in columns]

        data = {"activityLabel": activity_label, "columns": json.dumps(cols), "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during new log. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def new_log_entry(self, activity_label: str, values: Dict[str, object]) -> model.ServerMessage:
        """
        Creates a new log entry.

        Args:
            activity_label: The activity unique identifier.
            values: Dictionary in which the key is the column label and value is the entry value.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._sdk._server}/app/api/newLogEntry'

        data = {"logName": activity_label,
                "columns": json.dumps(values),
                "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

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
        # date  a partir desta data
        # date em branco eh tudo
        url = f'{self._sdk._server}/app/api/log/read'

        data = {"activityLabel": activity_label, "date": date, "access_token": self.access_token}
        with requests.get(url, params=data) as req:
            if req.status_code == 200:
                # TODO: Improve the way data is returned.
                return [entry.get('columns') for entry in json.loads(req.json()['message'])]
            else:
                try:
                    message = 'Error during log read. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log read. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

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
        url = f'{self._sdk._server}/app/api/log/delete'

        data = {"activityLabel": activity_label, "access_token": self.access_token}
        with requests.post(url, data=data) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during log delete. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log delete. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

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
        url = f'{self._sdk._server}/app/api/newArtifact'

        data = {
            "taskId": task_id,
            "name": artifact_name,
            "access_token": self.access_token
        }

        files = {
            'body': (
                artifact_name, open(filepath, 'rb'),
                'application/octet-stream', {'Expires': '0'}
            )
        }

        with requests.post(url, data=data, files=files) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during artifact posting. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact posting. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def list_artifacts(self) -> List[model.Artifact]:
        """
        List all artifacts available for the organization.

        Returns:
            List of artifacts. See [Artifact][botcity.maestro.model.Artifact]
        """
        url = f'{self._sdk._server}/app/api/artifact/list'

        data = {
            "access_token": self.access_token
        }

        with requests.get(url, params=data) as req:
            if req.status_code == 200:
                data = json.loads(req.text)
                message = data.get("message", "")
                if not message:
                    return []

                return [model.Artifact.from_dict(a) for a in json.loads(message)]
            else:
                try:
                    message = 'Error during artifact listing. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact listing. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def get_artifact(self, artifact_id: int) -> Tuple[str, bytes]:
        """
        Retrieve an artifact from the BotMaestro portal.

        Args:
            artifact_id: The artifact unique identifier.

        Returns:
            Tuple containing the artifact name and an array of bytes which are the binary content of the artifact.
        """
        url = f'{self._sdk._server}/app/api/artifact/get'

        data = {"id": artifact_id, "access_token": self.access_token}

        with requests.get(url, params=data) as req:
            if req.status_code == 200:
                h_content = req.headers['Content-Disposition']

                filename = h_content[h_content.rfind('=') + 2:-1]
                filename = filename[:filename.rfind('_')] + filename[filename.rfind('.'):]
                return filename, req.content
            else:
                try:
                    message = 'Error during artifact get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def error(self, task_id: int, exception: Exception, screenshot=None, attachments=None, tags=None):
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

    def get_credential(self, label: str, key: str):
        """
        Get value in key inside credentials
        Args:
            label: Credential set name
            key: Key name within the credential set

        Returns:
            Key value that was requested
        """
        raise NotImplementedError

    def create_credential(self, label: str, key: str, value):
        """
        Create credential
        Args:
            label: Credential set name
            key: Key name within the credential set
            value: Credential value
        """
        raise NotImplementedError

    def create_datapool(self, pool):
        raise NotImplementedError

    def get_datapool(self, label: str):
        raise NotImplementedError
