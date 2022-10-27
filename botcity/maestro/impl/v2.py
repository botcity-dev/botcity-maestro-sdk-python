import json
import traceback
from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

import requests
from requests_toolbelt import MultipartEncoder

from .. import model
from .interface import BotMaestroSDKInterface


class BotMaestroSDKV2(BotMaestroSDKInterface):

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

    def _headers(self) -> Dict:
        """The HTTP header for BotCity Maestro communication"""
        return {'Content-Type': 'application/json', "token": self.access_token, "organization": self._login}

    def login(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Obtain an access token with the configured BotMaestro portal.

        Arguments are optional and can be used to configure or overwrite the object instantiation values.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        """
        url = f'{self._server}/api/v2/workspace/login'
        data = {"login": self._login, "key": self._key}
        headers = {'Content-Type': 'application/json'}

        with requests.post(url, data=json.dumps(data), headers=headers) as req:
            if req.status_code == 200:
                self.access_token = req.json()['accessToken']
            else:
                raise ValueError('Error during login. Server returned %d. %s' % (req.status_code, req.text))

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

        with requests.post(url, json=data, headers=self._headers()) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:

                raise ValueError('Error during alert. %s', req.text)

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
        with requests.post(url, json=data, headers=self._headers()) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )
            payload = json.dumps({"message": req.text, "type":  req.status_code})
            return model.ServerMessage.from_json(payload=payload)

    def create_task(self, activity_label: str, parameters: Dict[str, object],
                    test: bool = False) -> model.AutomationTask:
        """
        Creates a task to be executed on the BotMaestro portal.

        Args:
            activity_label: The activity unique identified.
            parameters: Dictionary with parameters and values for this task.
            test: Whether or not the task is a test.

        Returns:
            Automation Task. See [AutomationTask][botcity.maestro.model.AutomationTask]
        """
        url = f'{self._server}/api/v2/task'
        data = {
            "activityLabel": activity_label, "test": test, "parameters": parameters
        }
        headers = self._headers()
        with requests.post(url, json=data, headers=headers) as req:
            if req.status_code == 200:
                return model.AutomationTask.from_json(req.text)
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
        url = f'{self._server}/api/v2/task/{task_id}'
        data = {"finishStatus": status, "finishMessage": message,
                "state": "FINISHED"}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers) as req:
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
        url = f'{self._server}/app/api/task/restart'

        data = {"id": task_id}
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
        url = f'{self._server}/api/v2/task/{task_id}'

        with requests.get(url, headers=self._headers()) as req:
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
        url = f'{self._server}/api/v2/log'

        cols = [asdict(c) for c in columns]

        data = {"activityLabel": activity_label, "columns": cols, 'organizationLabel': self._login}
        with requests.post(url, json=data, headers=self._headers()) as req:
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
        url = f'{self._server}/api/v2/log/{activity_label}/entry'

        with requests.post(url, json=values, headers=self._headers()) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type":  req.status_code})
            return model.ServerMessage.from_json(payload=payload)

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

        data = {"date": date}
        with requests.get(url, params=data, headers=self._headers()) as req:
            if req.status_code == 200:
                entries = req.json()
                return [column for column in entries.get('columns')]
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
        url = f'{self._server}/api/v2/log/{activity_label}'

        with requests.delete(url, headers=self._headers()) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during log delete. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log delete. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type":  req.status_code})
            return model.ServerMessage.from_json(payload=payload)

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
        artifact_id = self.create_artifact(task_id=task_id, name=artifact_name, filename=artifact_name)
        url = f'{self._server}/api/v2/artifact/log/{json.loads(artifact_id.payload)["id"]}'

        data = MultipartEncoder(
            fields={'file': (artifact_name, open(filepath, 'rb'))}
        )
        headers = {**self._headers(), 'Content-Type': data.content_type}
        with requests.post(url, data=data, headers=headers) as req:
            if req.status_code == 200:
                return artifact_id
            else:
                try:
                    message = 'Error during artifact posting. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact posting. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def create_artifact(self, task_id: int, name: str, filename: str) -> model.ServerMessage:
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
        with requests.post(url, json=data, headers=self._headers()) as req:
            if req.status_code == 200:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def list_artifacts(self, days: int = 7) -> List[model.Artifact]:
        """
        List all artifacts available for the organization.

        Returns:
            List of artifacts. See [Artifact][botcity.maestro.model.Artifact]
        """
        url = f'{self._server}/api/v2/artifact?size=5&page=0&sort=dateCreation,desc&days={days}'

        with requests.get(url, headers=self._headers()) as req:
            if req.status_code == 200:
                content = req.json()['content']
                response = [model.Artifact.from_dict(a) for a in content]
                for page in range(1, req.json()['totalPages']):
                    url = f'{self._server}/api/v2/artifact?size=5&page={page}&sort=dateCreation,desc&days={days}'
                    with requests.get(url, headers=self._headers()) as req:
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

    def get_artifact(self, artifact_id: int) -> Tuple[str, bytes]:
        """
        Retrieve an artifact from the BotMaestro portal.

        Args:
            artifact_id: The artifact unique identifier.

        Returns:
            Tuple containing the artifact name and an array of bytes which are the binary content of the artifact.
        """
        url = f'{self._server}/api/v2/artifact/{artifact_id}'

        with requests.get(url, headers=self._headers()) as req:
            if req.status_code == 200:
                payload = req.json()
                filename = payload['fileName']

                url = f'{self.server}/api/v2/artifact/{artifact_id}/file'
                with requests.get(url, headers=self._headers()) as req_file:
                    file_content = req_file.content

                return filename, file_content
            else:
                try:
                    message = 'Error during artifact get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def get_execution(self, task_id: Optional[str] = None) -> model.BotExecution:
        """
        Fetch the BotExecution object for a given task.

        Args:
            task_id (Optional[str], optional): The task ID. Defaults to None.

        Returns:
            model.BotExecution: The BotExecution information.
        """
        if not self.access_token and not self.RAISE_NOT_CONNECTED:
            return model.BotExecution("", "", "", {})

        task_id = task_id or self.task_id
        if not task_id:
            # If we are connected (access_token) or want to raise errors when disconnected
            # we show the error, otherwise we are working offline and just want to ignore this
            # but we will print a warning message for good measure
            raise ValueError("A task ID must be informed either via the parameter or the class property.")

        parameters = self.get_task(task_id).parameters

        execution = model.BotExecution(self.server, task_id, self.access_token, parameters)
        return execution

    def error(self, task_id: int, exception: Exception, screenshot=None, attachments=None, tags=None):
        """
        Creates a new error

        Args:
            task_id: The task unique identifier.
            exception: Error caught in except
            screenshot: File path for screenshot
            attachments: Object to filename and filepath.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._server}/api/v2/error'
        trace = " ".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        data = {'taskId': task_id, 'type': exception.__class__.__name__, 'message': str(exception),
                'stackTrace': trace, 'language': 'PYTHON', 'tags': tags}

        response = None
        with requests.post(url, json=data, headers=self._headers()) as req:
            if req.status_code == 201:
                response = req.json()
            else:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

        if screenshot:
            self.create_screenshot(error_id=response.get('id'), filepath=screenshot)

        if attachments:
            self.create_attachment(error_id=response.get('id'), attachments=attachments)

        return response

    def create_screenshot(self, error_id: int, filepath: str) -> None:
        """
           Creates a new screenshot in error

           Args:
               error_id: The error unique identifier.
               filepath: File path for screenshot
           Returns:
               None
           """
        url_screenshot = f'{self._server}/api/v2/error/{error_id}/screenshot'
        data_screenshot = MultipartEncoder(
            fields={'file': (filepath, open(filepath, 'rb'))}
        )
        headers = self._headers()
        headers['Content-Type'] = data_screenshot.content_type

        with requests.post(url_screenshot, data=data_screenshot, headers=headers) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def create_attachment(self, error_id: int, attachments: list):
        """
           Creates a new attachment in error

           Args:
               error_id: The error unique identifier.
               attachments: Object to filename and filepath.
           Returns:
               None
           """
        url_attachments = f'{self._server}/api/v2/error/{error_id}/attachments'

        for attachment in attachments:
            file = MultipartEncoder(
                fields={'file': (attachment['filename'], open(attachment['filepath'], 'rb'))}
            )
            headers = self._headers()
            headers['Content-Type'] = file.content_type
            with requests.post(url_attachments, data=file, headers=headers) as req:
                if req.status_code != 200:
                    try:
                        message = 'Error during new log entry. Server returned %d. %s' % (
                            req.status_code, req.json().get('message', ''))
                    except ValueError:
                        message = 'Error during new log entry. Server returned %d. %s' % (
                            req.status_code, req.text)
                    raise ValueError(message)

    def get_credential(self, label: str, key: str):
        """
        Get value in key inside credentials
        Args:
            label: Credential set name
            key: Key name within the credential set

        Returns:
            Key value that was requested
        """
        url = f'{self._server}/api/v2/credential/{label}/key/{key}'

        with requests.get(url, headers=self._headers()) as req:
            if req.status_code == 200:
                return req.text
            else:
                try:
                    message = 'Error during log read. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log read. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def create_credential(self, label: str, key: str, value):
        data = {
            'key': key,
            'value': value
        }
        url = f'{self._server}/api/v2/credential/{label}/key'

        with requests.post(url, json=data, headers=self._headers()) as req:
            if req.status_code != 201:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
