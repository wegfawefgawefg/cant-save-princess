from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict


class DialogueOption(TypedDict, total=False):
    label: str
    next: str
    action: str


class DialogueNode(TypedDict, total=False):
    text: str
    options: list[DialogueOption]
    end: bool


class DialogueTree(TypedDict, total=False):
    start: str
    backoutable: bool
    nodes: Dict[str, DialogueNode]


def initial_dialogues() -> Dict[str, DialogueTree]:
    # Simple two-part riddle
    return {
        "riddle1": {
            "start": "q1",
            "backoutable": True,
            "nodes": {
                "q1": {
                    "text": "I speak without a mouth and hear without ears. What am I?",
                    "options": [
                        {"label": "Echo", "next": "q2"},
                        {"label": "Wind", "next": "wrong"},
                        {"label": "Silence", "next": "wrong"},
                    ],
                },
                "q2": {
                    "text": "What has to be broken before you can use it?",
                    "options": [
                        {"label": "Egg", "action": "open_start_left_path", "next": "end"},
                        {"label": "Seal", "next": "wrong"},
                        {"label": "Promise", "next": "wrong"},
                    ],
                },
                "wrong": {
                    "text": "Incorrect. Think again.",
                    "options": [
                        {"label": "Back", "next": "q1"}
                    ],
                },
                "end": {
                    "text": "Well done. The path to the west opens.",
                    "options": [],
                    "end": True,
                },
            },
        }
    }
