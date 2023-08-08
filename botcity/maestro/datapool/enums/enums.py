import enum


class StateEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class ConsumptionPolicyEnum(str, enum.Enum):
    FIFO = "FIFO"
    LIFO = "LIFO"


class TriggerEnum(str, enum.Enum):
    ALWAYS = "ALWAYS"
    NEVER = "NEVER"
    NO_TASK_ACTIVE = "NO_TASK_ACTIVE"
