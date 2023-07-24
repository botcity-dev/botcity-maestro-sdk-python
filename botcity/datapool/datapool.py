

import json
from dataclasses import dataclass

import requests

from botcity.datapool.entry import DataPoolEntry, StateEnum
from botcity.maestro import BotMaestroSDK

from .enums import ConsumptionPolicyEnum, TriggerEnum


@dataclass
class DataPool:
    label: str
    default_activity: str
    consumption_policy: str = ConsumptionPolicyEnum.FIFO
    trigger: str = TriggerEnum.ALWAYS
    schema: list = None
    auto_retry: bool = True
    max_auto_retry: int = 0
    abort_on_error: bool = True
    max_errors_before_inactive: int = 0
    item_max_processing_time: int = 0
    datapool_id: str = None
    maestro: BotMaestroSDK = None
    active: bool = True
    count_pending: int = 0
    count_processing: int = 0
    count_done: int = 0
    count_error: int = 0
    count_timeout: int = 0
    avg_done: int = 0

    def to_dict(self):
        return {
            "label": self.label,
            "defaultActivity": self.default_activity,
            "consumptionPolicy": self.consumption_policy,
            "schema": self.schema,
            "trigger": self.trigger,
            "autoRetry": self.auto_retry,
            "maxAutoRetry": self.max_auto_retry,
            "abortOnError": self.abort_on_error,
            "maxErrorsBeforeInactive": self.max_errors_before_inactive,
            "itemMaxProcessingTime": self.item_max_processing_time,
            "active": self.active,
            "countPending": self.count_pending,
            "countProcessing": self.count_processing,
            "countDone": self.count_done,
            "countError": self.count_error,
            "countTimeout": self.count_timeout,
            "avgDone": self.avg_done
        }

    @staticmethod
    def from_json(payload: bytes, maestro) -> 'DataPool':
        values = json.loads(payload)
        datapool = DataPool(datapool_id=values.get("id"), label=values.get('label'),
                            default_activity=values.get("defaultActivity"),
                            consumption_policy=values.get("consumptionPolicy"), schema=values.get("schema"),
                            trigger=values.get("trigger"), auto_retry=values.get("autoRetry"),
                            max_auto_retry=values.get('maxAutoRetry'),
                            item_max_processing_time=values.get("itemMaxProcessingTime"),
                            max_errors_before_inactive=values.get("maxErrorsBeforeInactive"),
                            abort_on_error=values.get("abortOnError"), maestro=maestro,
                            count_error=values.get("countError"),
                            count_done=values.get("countDone"), count_processing=values.get("countProcessing"),
                            count_pending=values.get("countPending"),
                            count_timeout=values.get("countTimeout"), avg_done=values.get("avgDone")
                            )
        return datapool

    def _update_from_json(self, payload):
        values = json.loads(payload)
        self.datapool_id = values.get("id")
        self.label = values.get('label')
        self.default_activity = values.get("defaultActivity")
        self.consumption_policy = values.get("consumptionPolicy")
        self.schema = values.get("schema")
        self.trigger = values.get("trigger")
        self.auto_retry = values.get("autoRetry")
        self.max_auto_retry = values.get('maxAutoRetry')
        self.item_max_processing_time = values.get("itemMaxProcessingTime")
        self.max_errors_before_inactive = values.get("maxErrorsBeforeInactive")
        self.abort_on_error = values.get("abortOnError")
        self.active = values.get("active")
        self._update_count(payload=payload)

    def _update_count(self, payload):
        values = json.loads(payload)
        self.count_timeout = values.get("countTimeout")
        self.count_error = values.get("countError")
        self.count_done = values.get("countDone")
        self.count_processing = values.get("countProcessing")
        self.count_pending = values.get("countPending")
        self.avg_done = values.get("avgDone")

    def activate(self):
        data = self.to_dict()
        data['active'] = True
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.post(url, data=json.dumps(data), headers=self.maestro._impl._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return True
            req.raise_for_status()

    def deactivate(self):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'
        data = self.to_dict()
        data['active'] = False
        with requests.post(url, data=json.dumps(data), headers=self.maestro._impl._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return True
            req.raise_for_status()

    def is_activated(self):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}'

        with requests.get(url, headers=self.maestro._impl._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_from_json(payload=req.content)
                return self.active
            req.raise_for_status()

    def summary(self) -> dict:
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/summary'

        with requests.get(url, headers=self.maestro._impl._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                self._update_count(payload=req.content)
                return json.loads(req.content)
            req.raise_for_status()

    def create_entry(self, entry: DataPoolEntry):
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/push'

        with requests.post(url, data=entry.to_json(), headers=self.maestro._impl._headers(),
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
        with requests.post(url, data=data, headers=self.maestro._impl._headers(),
                           timeout=self.maestro.timeout) as req:
            if req.ok:
                entry.update_from_json(payload=req.content)
                return json.loads(req.content)
            req.raise_for_status()

    def next(self, task_id: int) -> DataPoolEntry:
        url = f'{self.maestro.server}/api/v2/datapool/{self.label}/pull'
        with requests.get(url, headers=self.maestro._impl._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                entry = DataPoolEntry(task_id=task_id)
                entry.maestro = self.maestro
                entry.update_from_json(payload=req.content)
                entry.state = StateEnum.PROCESSING
                try:
                    entry = entry.save()
                except Exception as error:
                    print(error)
                return entry
            req.raise_for_status()
