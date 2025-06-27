import enum


class StateEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELED = "CANCELED"


class ConsumptionPolicyEnum(str, enum.Enum):
    FIFO = "FIFO"
    LIFO = "LIFO"


class TriggerEnum(str, enum.Enum):
    ALWAYS = "ALWAYS"
    NEVER = "NEVER"
    NO_TASK_ACTIVE = "NO_TASK_ACTIVE"


class FieldType(str, enum.Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    DOUBLE = "DOUBLE"


class ErrorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    BUSINESS = "BUSINESS"
