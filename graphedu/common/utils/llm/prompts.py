"""Prompt template utilities for LangChain.

This module provides utilities for generating and managing prompts,
including sequence generators and accumulated prompt templates.
"""

from collections.abc import Generator, Iterable
import logging

from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


def acc_seq_generator(start: int = 1) -> Generator[int]:
    """Generate an infinite integer sequence starting from start.

    Args:
        start: Starting value (default: 1).

    Returns:
        Generator yielding integers from [start, +∞).
    """
    ret = 1
    while True:
        yield ret
        ret += 1


def generate_acc_prompt(
    template: str | PromptTemplate,
    delimiter: str = "\n",
    **kwargs: list | Generator | Iterable,
):
    """Generate accumulated prompt from template.

    Args:
        template: Prompt template that will be repeated.
        delimiter: Separator between prompts (default: newline).
        **kwargs: Variable lists.

    Returns:
        Generated prompt string.

    Raises:
        ValueError: If template variables and kwargs don't match.
    """
    # 1 处理 template
    if isinstance(template, str):
        template = PromptTemplate.from_template(template)
    # 2 查询可用的变量
    template_variables = set(template.input_variables)
    input_variables = set(template.input_variables)
    # 检查 input_variables >= template_variables
    if not template_variables.issubset(input_variables):
        raise ValueError(f"Template variables {template_variables} not match kwargs {input_variables}")
    # 3 生成
    ret = []
    keys = kwargs.keys()
    iters = kwargs.values()
    for values in zip(*iters, strict=False):
        new_kwargs = dict(zip(keys, values, strict=False))
        ret.append(template.format(**new_kwargs))
    return delimiter.join(ret)
