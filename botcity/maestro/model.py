import enum
import json
from typing import Dict
from dataclasses import dataclass, asdict


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
    """
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


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
        type: The message type. See [ServerMessageType][botcity.maestro.ServerMessageType]
        payload:
    """
    message: str
    type: ServerMessageType
    payload: str

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
        activity_id: Identifier of the activity.
        agent_id:  Identifier of the agent which created the task.
        user_creation_id: Identifier of the user which created the task.
        org_creation_id: Identifier of the organization which created the task.
        date_creation: Datetime information of when this task was created.
        date_last_modified: Datetime information of when this task was last modified.
        test: Whether or not this task was a test.
    """
    id: int
    state: AutomationTaskState
    parameters: Dict[str, object]
    activity_id: int
    agent_id: int
    user_creation_id: int
    org_creation_id: int
    date_creation: str
    date_last_modified: str
    test: bool

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
        activity_id = data.get("activityId")
        agent_id = data.get("agentId")
        user_creation_id = data.get("userCreationId")
        org_creation_id = data.get("organizationCreationId")
        date_creation = data.get("dateCreation")
        date_last_modified = data.get("dateLastModified")
        test = data.get("test")
        return AutomationTask(id=uid, state=state, parameters=parameters, activity_id=activity_id,
                              agent_id=agent_id, user_creation_id=user_creation_id,
                              org_creation_id=org_creation_id, date_creation=date_creation,
                              date_last_modified=date_last_modified, test=test)


@dataclass
class Column:
    """
    Representation of a Log column.

    Attributes:
        name: The column display name.
        label: The column unique identifier.
        width: The suggested log column width when rendering it on the BotMaestro portal.
    """
    name: str
    label: str
    width: int


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
