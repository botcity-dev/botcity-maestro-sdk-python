import json
from dataclasses import dataclass, field
from typing import List, Optional, Union

import requests

from .entry import DataPoolEntry
from .enums import ConsumptionPolicyEnum, FieldType, StateEnum, TriggerEnum


@dataclass
class SchemaField:
    label: str = None
    type: FieldType = None
    unique_id: bool = False
    display_value: bool = False


@dataclass
class DataPool:
    label: str
    name: str = None
    default_automation: str = None
    consumption_policy: str = ConsumptionPolicyEnum.FIFO
    trigger: str = TriggerEnum.NEVER
    schema: List[SchemaField] = field(default_factory=list)
    auto_retry: bool = True
    max_auto_retry: int = 0
    abort_on_error: bool = True
    max_errors_before_inactive: int = 0
    enable_processing_time: bool = True
    item_max_processing_time: int = 0
    datapool_id: str = None
    maestro: 'BotMaestroSDK' = None  # noqa: F821
    active: bool = True
    repository_label: str = "DEFAULT"

    def to_dict(self):
        """
        Get all properties class in dict.

        Returns: dict

        """
        schema = [
            {
                "label": field.label,
                "type": field.type,
                "uniqueId": field.unique_id,
                "displayValue": field.display_value,
            } for field in self.schema
        ]

        return {
            "label": self.label,
            "name": self.name,
            "defaultAutomation": self.default_automation,
            "consumptionPolicy": self.consumption_policy,
            "schema": schema,
            "trigger": self.trigger,
            "autoRetry": self.auto_retry,
            "maxAutoRetry": self.max_auto_retry,
            "abortOnError": self.abort_on_error,
            "maxErrorsBeforeInactive": self.max_errors_before_inactive,
            "enableProcessingTime": self.enable_processing_time,
            "itemMaxProcessingTime": self.item_max_processing_time,
            "active": self.active,
            "repositoryLabel": self.repository_label
        }

    @staticmethod
    def from_json(payload: bytes, maestro: 'BotMaestroSDK') -> 'DataPool':  # noqa: F821
        """
        Instantiate class by payload to request maestro.

        Args:
            payload: Response to maestro.
            maestro: Instance maestro class.

        Returns:
            Datapool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool].

        """
        values = json.loads(payload)
        datapool = DataPool(datapool_id=values.get("id"), label=values.get("label"), name=values.get("name"),
                            default_automation=values.get("defaultActivity"),
                            consumption_policy=values.get("consumptionPolicy"),
                            schema=DataPool._convert_schema_fields(values.get("schema")),
                            trigger=values.get("trigger"), auto_retry=values.get("autoRetry"),
                            max_auto_retry=values.get("maxAutoRetry"),
                            enable_processing_time=values.get("enableProcessingTime"),
                            item_max_processing_time=values.get("itemMaxProcessingTime"),
                            max_errors_before_inactive=values.get("maxErrorsBeforeInactive"),
                            abort_on_error=values.get("abortOnError"),
                            repository_label=values.get("repositoryLabel"), maestro=maestro,
                            )
        return datapool

    def _update_from_json(self, payload: str):
        """

        Update properties by response endpoint Maestro.
        Args:
            payload: Response to endpoint Maestro.

        Returns: None

        """
        values = json.loads(payload)
        self.datapool_id = values.get("id")
        self.label = values.get("label")
        self.name = values.get("name")
        self.default_automation = values.get("defaultActivity")
        self.consumption_policy = values.get("consumptionPolicy")
        self.schema = self._convert_schema_fields(values.get("schema"))
        self.trigger = values.get("trigger")
        self.auto_retry = values.get("autoRetry")
        self.max_auto_retry = values.get("maxAutoRetry")
        self.enable_processing_time = values.get("enableProcessingTime")
        self.item_max_processing_time = values.get("itemMaxProcessingTime")
        self.max_errors_before_inactive = values.get("maxErrorsBeforeInactive")
        self.abort_on_error = values.get("abortOnError")
        self.active = values.get("active")
        self.repository_label = values.get("repositoryLabel")

    @staticmethod
    def _convert_schema_fields(schema_data: list) -> List[SchemaField]:
        """
        Converts schema fields from API response to SchemaField objects.

        Args:
            schema_data (list): List of schema field dictionaries from the API response.

        Returns:
            List[SchemaField]: List of SchemaField objects.
        """
        return [
            SchemaField(
                label=field.get("label"),
                type=field.get("type"),
                unique_id=field.get("uniqueId"),
                display_value=field.get("displayValue"),
            ) for field in schema_data
        ]

    def activate(self):
        """
        Enables the DataPool in Maestro.
        Returns: None

        """
        data = self.to_dict()
        data['active'] = True
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.post(url, data=json.dumps(data), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout, verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return True
            req.raise_for_status()

    def deactivate(self):
        """
        Disable DataPool in Maestro.
        Returns: None

        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'
        data = self.to_dict()
        data['active'] = False
        with requests.post(url, data=json.dumps(data), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout, verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return True
            req.raise_for_status()

    def is_active(self) -> bool:
        """
        Check if the DataPool is active.
        Returns: bool

        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                          verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return self.active
            req.raise_for_status()

    def summary(self) -> dict:
        """
        Get the DataPool counters.
        Returns: dict

        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/summary'

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                          verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                return json.loads(req.content)
            req.raise_for_status()

    def create_entry(self, entry: DataPoolEntry) -> DataPoolEntry:
        """
        Create an entry by DataPool

        Args:
            entry: Instance of DataPoolEntry

        Returns:
            DataPoolEntry: the entry that was created.

        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/push'

        with requests.post(url, data=entry.to_json(), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout, verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                entry.update_from_json(payload=req.content)
                return entry
            req.raise_for_status()

    def get_entry(self, entry_id: str) -> DataPoolEntry:
        """Fetch an entry from the DataPool by its ID.

        Args:
            entry_id (str): The ID of the entry to fetch.

        Returns:
            DataPoolEntry: The entry that was fetched.
        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/entry/{entry_id}'
        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                          verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                entry = DataPoolEntry()
                entry.update_from_json(payload=req.content)
                entry.maestro = self.maestro
                return entry
            req.raise_for_status()

    def cancel_entry(self, entry_id: str, finish_message: str = "") -> DataPoolEntry:
        """
        Cancel an entry in the DataPool by its ID.

        Only entries in 'PENDING' state can be canceled.

        Args:
            entry_id (str): The ID of the entry to cancel.
            finish_message (Optional, str): A message to be associated with this action.

        Returns:
            DataPoolEntry: The entry that was canceled.
        """
        entry = self.get_entry(entry_id)
        if entry.state != StateEnum.PENDING:
            raise ValueError(f"Cancel operation is only allowed for entries in 'PENDING' state. "
                             f"Current entry state: {entry.state}.")

        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/entry/{entry_id}/cancel'
        data = {"state": StateEnum.CANCELED, "message": finish_message}

        with requests.put(url, data=json.dumps(data), headers=self.maestro._headers(),
                          timeout=self.maestro.timeout, verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                entry = DataPoolEntry()
                entry.update_from_json(payload=req.content)
                entry.maestro = self.maestro
                return entry
            req.raise_for_status()

    def delete_entry(self, entry_id: str) -> None:
        """
        Delete an entry in the DataPool by its ID.

        Only entries in these states can be deleted: 'PENDING', 'CANCELED', 'DONE', 'ERROR'.

        Args:
            entry_id (str): The ID of the entry to delete.

        Returns: None
        """
        entry = self.get_entry(entry_id)
        valid_states = [StateEnum.PENDING, StateEnum.CANCELED, StateEnum.DONE, StateEnum.ERROR]

        if entry.state not in valid_states:
            raise ValueError(f"Deletion is only allowed for the following states: {', '.join(valid_states)}. "
                             f"Current entry state: {entry.state}.")

        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/entry/{entry_id}'
        with requests.delete(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                             verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.ok:
                return
            req.raise_for_status()

    def is_empty(self) -> bool:
        """Checks if the DataPool is empty.

        Returns:
            bool: True if the DataPool is empty, False otherwise.
        """
        summary = self.summary()
        if summary.get("countPending", 0) == 0:
            return True
        return False

    def has_next(self) -> bool:
        """Checks if there are pending items in the DataPool.

        Returns:
            bool: True if there are pending items, False otherwise.
        """
        return not self.is_empty()

    def next(self, task_id: Optional[str]) -> Union[DataPoolEntry, None]:
        """Fetch the next pending entry.

        Args:
            task_id: TaskId to be associated with this entry.

        Returns:
            DataPoolEntry or None: The next pending entry, or None if there are no pending entries.

        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/pull'
        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                          verify=self.maestro.VERIFY_SSL_CERT) as req:
            if req.status_code == 204:
                return None

            if req.ok:
                entry = DataPoolEntry()
                entry.update_from_json(payload=req.content)
                entry.task_id = str(task_id)
                entry.maestro = self.maestro
                return entry

            req.raise_for_status()

    def _delete(self):
        """
        Delete DataPool in Maestro.
        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'
        with requests.delete(url, headers=self.maestro._headers(), timeout=self.maestro.timeout,
                             verify=self.maestro.VERIFY_SSL_CERT) as req:
            req.raise_for_status()
