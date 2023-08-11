import json
from dataclasses import dataclass
from typing import Union, Optional

import requests

from .entry import DataPoolEntry
from .enums import ConsumptionPolicyEnum, TriggerEnum


@dataclass
class DataPool:
    label: str
    default_automation: str
    consumption_policy: str = ConsumptionPolicyEnum.FIFO
    trigger: str = TriggerEnum.NEVER
    schema: list = None
    auto_retry: bool = True
    max_auto_retry: int = 0
    abort_on_error: bool = True
    max_errors_before_inactive: int = 0
    item_max_processing_time: int = 0
    datapool_id: str = None
    maestro: 'BotMaestroSDKInterface' = None  # noqa: F821
    active: bool = True

    def to_dict(self):
        """
        Get all properties class in dict.

        Returns: dict

        """
        return {
            "label": self.label,
            "defaultAutomation": self.default_automation,
            "consumptionPolicy": self.consumption_policy,
            "schema": self.schema,
            "trigger": self.trigger,
            "autoRetry": self.auto_retry,
            "maxAutoRetry": self.max_auto_retry,
            "abortOnError": self.abort_on_error,
            "maxErrorsBeforeInactive": self.max_errors_before_inactive,
            "itemMaxProcessingTime": self.item_max_processing_time,
            "active": self.active,
        }

    @staticmethod
    def from_json(payload: bytes, maestro: 'BotMaestroSDKInterface') -> 'DataPool':  # noqa: F821
        """
        Instantiate class by payload to request maestro.

        Args:
            payload: Response to maestro.
            maestro: Instance maestro class.

        Returns:
            Datapool instance. See [DataPool][ [DataPool][botcity.maestro.datapool.DataPool].

        """
        values = json.loads(payload)
        datapool = DataPool(datapool_id=values.get("id"), label=values.get('label'),
                            default_automation=values.get("defaultActivity"),
                            consumption_policy=values.get("consumptionPolicy"), schema=values.get("schema"),
                            trigger=values.get("trigger"), auto_retry=values.get("autoRetry"),
                            max_auto_retry=values.get('maxAutoRetry'),
                            item_max_processing_time=values.get("itemMaxProcessingTime"),
                            max_errors_before_inactive=values.get("maxErrorsBeforeInactive"),
                            abort_on_error=values.get("abortOnError"), maestro=maestro,
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
        self.label = values.get('label')
        self.default_automation = values.get("defaultActivity")
        self.consumption_policy = values.get("consumptionPolicy")
        self.schema = values.get("schema")
        self.trigger = values.get("trigger")
        self.auto_retry = values.get("autoRetry")
        self.max_auto_retry = values.get('maxAutoRetry')
        self.item_max_processing_time = values.get("itemMaxProcessingTime")
        self.max_errors_before_inactive = values.get("maxErrorsBeforeInactive")
        self.abort_on_error = values.get("abortOnError")
        self.active = values.get("active")

    def activate(self):
        """
        Enables the DataPool in Maestro.
        Returns: None

        """
        data = self.to_dict()
        data['active'] = True
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.post(url, data=json.dumps(data), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout) as req:
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
                           timeout=self.maestro.timeout) as req:
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

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
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

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
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
                           timeout=self.maestro.timeout) as req:
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
        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                entry = DataPoolEntry()
                entry.update_from_json(payload=req.content)
                entry.maestro = self.maestro
                return entry
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
        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
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
        with requests.delete(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            req.raise_for_status()
