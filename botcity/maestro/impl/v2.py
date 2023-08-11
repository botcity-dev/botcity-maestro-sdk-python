import datetime
import json
import os
import platform
import traceback
from dataclasses import asdict
from io import IOBase, StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import distro
import importlib_metadata
import requests
from requests_toolbelt import MultipartEncoder

from .. import model
from .interface import BotMaestroSDKInterface
from ..datapool import DataPool


class BotMaestroSDKV2(BotMaestroSDKInterface):

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

    def _headers(self) -> Dict:
        """The HTTP header for BotCity Maestro communication"""
        return {
            "Content-Type": "application/json",
            "token": self._sdk.access_token,
            "organization": self._sdk.organization
        }

    def login(self, server: Optional[str] = None, login: Optional[str] = None, key: Optional[str] = None):
        """
        Obtain an access token with the configured BotMaestro portal.

        Arguments are optional and can be used to configure or overwrite the object instantiation values.

        Args:
            server: The server IP or name
            login: The username provided via server configuration. Available under `Dev. Environment`
            key: The access key provided via server configuration. Available under `Dev. Environment`

        """
        url = f'{self._sdk._server}/api/v2/workspace/login'
        data = {"login": self._sdk.organization, "key": self._sdk._key}
        headers = {'Content-Type': 'application/json'}

        with requests.post(url, data=json.dumps(data), headers=headers, timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/alerts'

        data = {"taskId": task_id, "title": title,
                "message": message, "type": alert_type}

        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/message'

        if not group:
            group = ""

        data = {"emails": email, "logins": users, "subject": subject, "body": body,
                "type": msg_type, "group": group}
        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if req.status_code != 200:
                raise ValueError(
                    'Error during message. Server returned %d. %s' %
                    (req.status_code, req.json().get('message', ''))
                )
            payload = json.dumps({"message": req.text, "type": req.status_code})
            return model.ServerMessage.from_json(payload=payload)

    def create_task(self, activity_label: str, parameters: Dict[str, object],
                    test: bool = False, priority: int = 0, min_execution_date=None) -> \
            model.AutomationTask:
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
        url = f'{self._sdk._server}/api/v2/task'

        data = {
            "activityLabel": activity_label, "test": test, "parameters": parameters, "priority": priority,
        }

        if min_execution_date is not None:
            if not isinstance(min_execution_date, datetime.datetime):
                raise ValueError(f"Arg 'min_execution_date' is not datetime. Type {type(min_execution_date)}")
            data["minExecutionDate"] = min_execution_date.isoformat()

        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/task/{task_id}'
        data = {"finishStatus": status, "finishMessage": message,
                "state": "FINISHED"}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/task/{task_id}'
        data = {"state": "START"}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/task/{task_id}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
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

    def interrupt_task(self, task_id: str) -> model.ServerMessage:
        """
        Request the interruption of a given task.

        Args:
            task_id (str): The task unique identifier.

        Returns:
            Server response message. See [ServerMessage][botcity.maestro.model.ServerMessage]
        """
        url = f'{self._sdk._server}/api/v2/task/{task_id}'
        data = {"interrupted": True}
        headers = self._headers()
        with requests.post(url, json=data, headers=headers, timeout=self.timeout) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                try:
                    message = 'Error during task finish. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during task finish. Server returned %d. %s' % (req.status_code, req.text)
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
        url = f'{self._sdk._server}/api/v2/log'

        cols = [asdict(c) for c in columns]

        data = {"activityLabel": activity_label, "columns": cols, 'organizationLabel': self._sdk.organization}
        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/log/{activity_label}/entry'

        with requests.post(url, json=values, headers=self._headers(), timeout=self.timeout) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type": req.status_code})
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
        url = f'{self._sdk._server}/api/v2/log/{activity_label}'

        days = 365  # 1 year is enough
        if date:
            days = (datetime.datetime.now()-datetime.datetime.strptime(date, "%d/%m/%Y")).days + 1

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                log = req.json()
                columns = log.get('columns')
                if not columns:
                    raise ValueError('Malformed log. No columns available.')
                names_for_labels = {c['label']: c['name'] for c in columns}
                url = f'{self._sdk._server}/api/v2/log/{activity_label}/entry-list'

                data = {"days": days}
                with requests.get(url, params=data, headers=self._headers(), timeout=self.timeout) as entry_req:
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
        url = f'{self._sdk._server}/api/v2/log/{activity_label}'

        with requests.delete(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.status_code != 200:
                try:
                    message = 'Error during log delete. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log delete. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)
            payload = json.dumps({"message": req.text, "type": req.status_code})
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
        url = f'{self._sdk._server}/api/v2/artifact/log/{json.loads(artifact_id.payload)["id"]}'

        with open(filepath, 'rb') as f:
            data = MultipartEncoder(
                fields={'file': (artifact_name, f)}
            )
            headers = {**self._headers(), 'Content-Type': data.content_type}
            with requests.post(url, data=data, headers=headers, timeout=self.timeout) as req:
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
        url = f'{self._sdk._server}/api/v2/artifact'
        data = {'taskId': task_id, 'name': name, 'filename': filename}
        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
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
        url = f'{self._sdk._server}/api/v2/artifact?size=5&page=0&sort=dateCreation,desc&days={days}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                content = req.json()['content']
                response = [model.Artifact.from_dict(a) for a in content]
                for page in range(1, req.json()['totalPages']):
                    url = f'{self._sdk._server}/api/v2/artifact?size=5&page={page}&sort=dateCreation,desc&days={days}'
                    with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
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
        url = f'{self._sdk._server}/api/v2/artifact/{artifact_id}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                payload = req.json()
                filename = payload['fileName']

                url = f'{self.server}/api/v2/artifact/{artifact_id}/file'
                with requests.get(url, headers=self._headers(), timeout=self.timeout) as req_file:
                    file_content = req_file.content

                return filename, file_content
            else:
                try:
                    message = 'Error during artifact get. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during artifact get. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

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
        url = f'{self._sdk._server}/api/v2/error'
        trace = " ".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

        if not tags:
            tags = dict()

        default_tags = self._get_default_error_tags()
        default_tags.update(tags)
        tags = default_tags

        data = {'taskId': task_id, 'type': exception.__class__.__name__, 'message': str(exception),
                'stackTrace': trace, 'language': 'PYTHON', 'tags': tags}

        response = None
        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
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
        url_screenshot = f'{self._sdk._server}/api/v2/error/{error_id}/screenshot'
        filepath = os.path.expandvars(os.path.expanduser(filepath))

        with open(filepath, 'rb') as f:
            data_screenshot = MultipartEncoder(
                fields={'file': (Path(filepath).name, f)}
            )
            headers = self._headers()
            headers['Content-Type'] = data_screenshot.content_type

            with requests.post(url_screenshot, data=data_screenshot, headers=headers, timeout=self.timeout) as req:
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
        url_attachments = f'{self._sdk._server}/api/v2/error/{error_id}/attachments'

        file = MultipartEncoder(
            fields={'file': (filename, buffer)}
        )
        headers = self._headers()
        headers['Content-Type'] = file.content_type
        with requests.post(url_attachments, data=file, headers=headers, timeout=self.timeout) as req:
            if not req.ok:
                try:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during new log entry. Server returned %d. %s' % (
                        req.status_code, req.text)
                raise ValueError(message)

    def get_credential(self, label: str, key: str) -> str:
        """
        Get value in key inside credentials
        Args:
            label: Credential set name
            key: Key name within the credential set

        Returns:
            value (str): Key value that was requested
        """
        url = f'{self._sdk._server}/api/v2/credential/{label}/key/{key}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                return str(req.text)
            else:
                try:
                    message = 'Error during log read. Server returned %d. %s' % (
                        req.status_code, req.json().get('message', ''))
                except ValueError:
                    message = 'Error during log read. Server returned %d. %s' % (req.status_code, req.text)
                raise ValueError(message)

    def create_credential(self, label: str, key: str, value: str):
        """Create a new key/value entry for a credential set.

        Args:
            label (str): The credential set label
            key (str): The key identifier for this credential
            value (str): The value associated with this key

        """
        credential = self._get_credential_by_label(label=label)

        if credential is None:
            response = self._create_credential_by_label(label=label, key=key, value=value)
            if response is None:
                raise ValueError('Error during create credential.')
            return response.to_json()
        data = {
            'key': key,
            'value': value
        }
        url = f'{self._sdk._server}/api/v2/credential/{label}/key'
        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if not req.ok:
                req.raise_for_status()

    def _get_credential_by_label(self, label):
        """
        Get dict in key inside credentials
        Args:
            label: Credential set name
        Returns:
            Credential dict
        """
        url = f'{self._sdk._server}/api/v2/credential/{label}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                return None

    def _create_credential_by_label(self, label: str, key: str, value):
        data = {
            'label': label,
            'secrets': [
                {'key': key, 'value': value, 'valid': True}
            ]
        }
        url = f'{self._sdk._server}/api/v2/credential'

        with requests.post(url, json=data, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                return model.ServerMessage.from_json(req.text)
            else:
                return None

    def create_datapool(self, pool) -> DataPool:
        """
        Create a new datapool on the BotMaestro portal.

        Args:
            pool: The DataPool [DataPool][botcity.maestro.datapool.DataPool] instance.

        Returns:
            Datapool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool] instance.
        """
        url = f'{self._sdk.server}/api/v2/datapool'
        pool.maestro = self
        with requests.post(url, data=json.dumps(pool.to_dict()), headers=self._headers(),
                           timeout=self.timeout) as req:
            if req.ok:
                return pool
            req.raise_for_status()

    def get_datapool(self, label: str) -> DataPool:
        """
        Get datapool on the BotMaestro portal.

        Args:
            label: Label DataPool.

        Returns:
            Datapool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool].
        """
        url = f'{self._sdk._server}/api/v2/datapool/{label}'

        with requests.get(url, headers=self._headers(), timeout=self.timeout) as req:
            if req.ok:
                return DataPool.from_json(payload=req.content, maestro=self)
            req.raise_for_status()
