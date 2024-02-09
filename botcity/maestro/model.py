import enum
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


class AlertType(str, enum.Enum):
    """
    Type of alerts to be emitted.

    Attributes:
        INFO (str): Information alert type
        WARN (str): Warning alert type
        ERROR (str): Error alert type
    """
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class MessageType(str, enum.Enum):
    """
    Type of message body.

    Attributes:
        TEXT (str): Plain text message body
        HTML (str): HTML message body
    """
    TEXT = "TEXT"
    HTML = "HTML"


class AutomationTaskState(str, enum.Enum):
    """
    State of a Task.

    Attributes:
        START (str): The task was started.
        RUNNING (str): The task is running.
        FINISHED (str): The task is finished.
        CANCELED (str): The task was canceled.
    """
    START = "START"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"


class AutomationTaskFinishStatus(str, enum.Enum):
    """
    Finish status of a task.

    Attributes:
        SUCCESS (str): The task finished successfully.
        FAILED (str): The task failed to finish.
        PARTIALLY_COMPLETED (str): The task completed part of the expected steps.
    """
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


class ServerMessageType(str, enum.Enum):
    """
    The server message type.

    Attributes:
        SUCCESS (str): Success message
        ERROR (str): Error message
    """
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ServerMessage:
    """
    Server response message.

    Attributes:
        message: The response message sent by the BotMaestro portal.
        type: The message type. See [ServerMessageType][botcity.maestro.model.ServerMessageType]
        payload:
    """
    message: str = ""
    type: ServerMessageType = ServerMessageType.ERROR
    payload: str = ""

    def to_json(self) -> str:
        """

        Returns:
            JSON string representation of this object.
        """
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(payload: str) -> 'ServerMessage':
        """
        Instantiate a `ServerMessage` object from a JSON payload
        obtained from the BotMaestro portal.

        Args:
            payload: A JSON string containing message and type.

        Returns:
            Server response message instance.
        """
        data = json.loads(payload)
        msg = data.get('message')
        tp = data.get('type')
        return ServerMessage(msg, tp, payload)


@dataclass
class AutomationTask:
    """
    Automation Task.

    Attributes:
        id: The task unique identifier.
        state: The task state. See [AutomationTaskState][botcity.maestro.model.AutomationTaskState].
        parameters: Dictionary with parameters and values for this task.
        input_file: The input file for this task.
        activity_id: Identifier of the automation. (Deprecated)
        activity_label: Automation label identifier.
        agent_id:  Identifier of the agent which created the task.
        user_creation_id: Identifier of the user which created the task.
        user_creation_name: Name of the user which created the task.
        org_creation_id: Identifier of the organization which created the task.
        date_creation: Datetime information of when this task was created.
        date_last_modified: Datetime information of when this task was last modified.
        finish_status: The finish status of this task. See
            [AutomationTaskFinishStatus][botcity.maestro.model.AutomationTaskFinishStatus].
        finish_message: The finish message of this task.
        test: Whether or not this task was a test.
        interrupted: Whether or not this task received an interrupt request.
        killed: Whether or not this task received a termination request.
        machine_id: Identifier of the machine that performed the automation.
    """
    id: int = 0
    state: AutomationTaskState = AutomationTaskState.START
    parameters: Dict[str, object] = None
    input_file: 'Artifact' = None
    agent_id: int = 0
    user_email: str = None
    user_creation_name: str = None
    organization_label: str = None
    date_creation: str = None
    date_last_modified: str = None
    finish_status: AutomationTaskFinishStatus = AutomationTaskFinishStatus.FAILED
    finish_message: str = None
    test: bool = False
    machine_id: str = None
    activity_label: str = None
    interrupted: bool = False
    min_execution_date: str = None
    killed: bool = False
    date_start_running: str = None
    priority: int = 0
    repository_label: str = None
    processed_items: int = 0
    failed_items: int = 0
    total_items: int = 0
    activity_name: str = None

    def to_json(self) -> str:
        """

        Returns:
            JSON string representation of this object.
        """
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(payload: str) -> 'AutomationTask':
        """
        Instantiate a `AutomationTask` object from a JSON payload
        obtained from the BotMaestro portal.

        Args:
            payload: A JSON string containing the required metadata.

        Returns:
            Automation Task instance.
        """
        data = json.loads(payload)
        uid = data.get("id")
        state = data.get("state")
        parameters = data.get("parameters")
        input_file = data.get("inputFile")
        if input_file:
            input_file = Artifact.from_dict(input_file)
        agent_id = data.get("agentId")
        user_email = data.get("userEmail")
        user_creation_name = data.get("userCreationName")
        organization_label = data.get("organizationLabel")
        date_creation = data.get("dateCreation")
        date_last_modified = data.get("dateLastModified")
        finish_status = data.get("finishStatus")
        finish_message = data.get("finishMessage")
        test = data.get("test", False)
        machine_id = data.get("machineId")
        activity_label = data.get("activityLabel")
        interrupted = data.get("interrupted", False)
        interrupted = False if interrupted is None else interrupted
        min_execution_date = data.get("minExecutionDate")
        killed = data.get("killed", False)
        killed = False if killed is None else killed
        date_start_running = data.get("dateStartRunning")
        priority = data.get("priority")
        repository_label = data.get("repositoryLabel")
        processed_items = data.get("processedItems")
        failed_items = data.get("failedItems")
        total_items = data.get("totalItems")
        activity_name = data.get("activityName")

        return AutomationTask(id=uid, state=state, parameters=parameters,
                              activity_label=activity_label,
                              input_file=input_file, agent_id=agent_id, user_email=user_email,
                              user_creation_name=user_creation_name, organization_label=organization_label,
                              date_creation=date_creation, date_last_modified=date_last_modified,
                              finish_status=finish_status, finish_message=finish_message,
                              test=test, machine_id=machine_id,
                              interrupted=interrupted, min_execution_date=min_execution_date, killed=killed,
                              date_start_running=date_start_running, priority=priority,
                              repository_label=repository_label,
                              processed_items=processed_items, failed_items=failed_items, total_items=total_items,
                              activity_name=activity_name)

    def is_interrupted(self) -> bool:
        """Whether or not this task received an interrupt request.

        Returns:
            bool: Whether or not this task received an interrupt request.
        """
        return self.interrupted


@dataclass
class Artifact:
    """
    Artifact.

    Attributes:
        id: The task unique identifier.
        type: The type of artifact.
        task_id: The task unique identifier.
        name: Display name for artifact.
        filename: File name as provided during upload.
        storage_filename: Internal file name.
        storage_filepath: Internal absolute path to file.
        organization: The organization unique identifier.
        user: The user unique identifier.
        date_creation: Datetime information of when this artifact was created.
    """
    id: int = 0
    type: str = None
    task_id: int = 0
    task_name: str = None
    name: str = None
    filename: str = None
    storage_filename: str = None
    storage_filepath: str = None
    organization: int = 0
    user: Optional[int] = 0
    date_creation: str = None

    def to_json(self) -> str:
        """

        Returns:
            JSON string representation of this object.
        """
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(payload: str) -> 'Artifact':
        """
        Instantiate a `Artifact` object from a JSON payload
        obtained from the BotMaestro portal.

        Args:
            payload: A JSON string containing the required metadata.

        Returns:
            Artifact instance.
        """
        data = json.loads(payload)
        return Artifact.from_dict(data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Artifact':
        """
        Instantiate a `Artifact` object from a dict payload obtained
        from the BotMaestro portal.

        Args:
            data: A dictionary containing the required metadata.

        Returns:
            Artifact instance.
        """
        uid = data.get("id", None)
        tp = data.get("type", None)
        task_id = data.get("taskId", None)
        name = data.get("name", None)
        filename = data.get("fileName", None)
        storage_filename = data.get("storageFileName", None)
        storage_filepath = data.get("storageFilePath", None)
        organization = data.get("organizationId", None)
        user = data.get("user", None)
        date_creation = data.get("dateCreation", None)
        task_name = data.get("taskName", None)

        return Artifact(
            id=uid, type=tp, task_id=task_id, name=name, filename=filename,
            storage_filename=storage_filename, storage_filepath=storage_filepath,
            organization=organization, user=user, date_creation=date_creation, task_name=task_name
        )


@dataclass
class Column:
    """
    Representation of a Log column.

    Attributes:
        name: The column display name.
        label: The column unique identifier.
        width: The suggested log column width when rendering it on the BotMaestro portal.
    """
    name: str = None
    label: str = None
    width: int = 0


@dataclass
class BotExecution:
    """
    Bot execution parameters.

    Attributes:
        server: The BotMaestro server hostname or IP.
        task_id: The task unique identifier.
        token: The access token to be used when communicating with the BotMaestro server.
        parameters: Dictionary with parameters and values for this task.
    """
    server: str
    task_id: str
    token: str
    parameters: Dict[str, object]
