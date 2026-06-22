from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from trustinspect.core.models import Observation, Target, TestCase


class ScannerAdapter(ABC):
    """Base class for execution engines integrated with TrustInspect."""

    @abstractmethod
    def run(self, target: Target, test_cases: Iterable[TestCase]) -> list[Observation]:
        raise NotImplementedError
