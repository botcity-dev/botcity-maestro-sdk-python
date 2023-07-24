import json
from dataclasses import dataclass
from typing import Union

import requests

from ..sdk import BotMaestroSDKInterface
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
    maestro: BotMaestroSDKInterface = None
    active: bool = True

    def to_dict(self):
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
    def from_json(payload: bytes, maestro: BotMaestroSDKInterface) -> 'DataPool':
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

    def _update_from_json(self, payload):
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
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'
        data = self.to_dict()
        data['active'] = False
        with requests.post(url, data=json.dumps(data), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return True
            req.raise_for_status()

    def is_activated(self):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return self.active
            req.raise_for_status()

    def summary(self) -> dict:
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/summary'

        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                return json.loads(req.content)
            req.raise_for_status()

    def create_entry(self, entry: DataPoolEntry):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/push'

        with requests.post(url, data=entry.to_json(), headers=self.maestro._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                entry.update_from_json(payload=req.content)
                return json.loads(req.content)
            req.raise_for_status()

    def is_empty(self):
        summary = self.summary()
        if summary.get("countPending", 0) == 0:
            return True
        return False

    def save_entry(self, entry: DataPoolEntry):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/entry/{entry.entry_id}'
        data = entry.json_to_update()
        with requests.post(url, data=data, headers=self.maestro._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                entry.update_from_json(payload=req.content)
                return json.loads(req.content)
            req.raise_for_status()

    def next(self, task_id: int) -> Union[DataPoolEntry, None]:
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/pull'
        with requests.get(url, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            if req.status_code == 204:
                return None

            if req.ok:
                entry = DataPoolEntry(task_id=task_id)
                entry.maestro = self.maestro
                entry.update_from_json(payload=req.content)
                return entry

            req.raise_for_status()
