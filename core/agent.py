"""Compatibility layer.

The real implementation now lives in `manufacturing_agent/`.
Keep this module tiny so beginners do not accidentally start reading the old
orchestration entrypoint first.
"""

from manufacturing_agent.agent import run_agent

__all__ = ["run_agent"]
