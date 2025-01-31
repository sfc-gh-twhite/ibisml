from __future__ import annotations

from typing import Any, Iterable

import ibisml as ml
from ibisml.core import Metadata, Step, Transform
from ibisml.select import SelectionType, selector

import ibis.expr.types as ir


class FillNA(Step):
    """A step for filling NULL values in the input with a specific value.

    Parameters
    ----------
    inputs
        A selection of columns to fillna.
    fill_value
        The fill value to use. Must be castable to the dtype of all columns in
        inputs.

    Examples
    --------
    >>> import ibisml as ml

    Fill all NULL values in numeric columns with 0.

    >>> step = ml.FillNA(ml.numeric(), 0)

    Fill all NULL values in specific columns with 1.

    >>> step = ml.FillNA(["x", "y"], 1)
    """

    def __init__(self, inputs: SelectionType, fill_value: Any):
        self.inputs = selector(inputs)
        self.fill_value = fill_value

    def _repr(self) -> Iterable[tuple[str, Any]]:
        yield ("", self.inputs)
        yield ("", self.fill_value)

    def fit(self, table: ir.Table, metadata: Metadata) -> Transform:
        columns = self.inputs.select_columns(table, metadata)
        return ml.transforms.FillNA({c: self.fill_value for c in columns})


class _BaseImpute(Step):
    def __init__(self, inputs: SelectionType):
        self.inputs = selector(inputs)

    def _repr(self) -> Iterable[tuple[str, Any]]:
        yield ("", self.inputs)

    def _stat(self, col: ir.Column) -> ir.Scalar:
        raise NotImplementedError

    def fit(self, table: ir.Table, metadata: Metadata) -> Transform:
        columns = self.inputs.select_columns(table, metadata)

        stats = (
            table.aggregate([self._stat(table[c]).name(c) for c in columns])
            .execute()
            .to_dict("records")[0]
        )
        return ml.transforms.FillNA(stats)


class ImputeMean(_BaseImpute):
    """A step for replacing NULL values in select columns with their
    respective mean in the training set.

    Parameters
    ----------
    inputs
        A selection of columns to impute. All columns must be numeric.

    Examples
    --------
    >>> import ibisml as ml

    Replace NULL values in all numeric columns with their respective means,
    computed from the training dataset.

    >>> step = ml.ImputeMean(ml.numeric())
    """

    def _stat(self, col: ir.Column) -> ir.Scalar:
        if not isinstance(col, ir.NumericColumn):
            raise ValueError(
                f"Cannot compute mean of {col.get_name()} - "
                "this column is not numeric"
            )
        return col.mean()


class ImputeMedian(_BaseImpute):
    """A step for replacing NULL values in select columns with their
    respective medians in the training set.

    Parameters
    ----------
    inputs
        A selection of columns to impute. All columns must be numeric.

    Examples
    --------
    >>> import ibisml as ml

    Replace NULL values in all numeric columns with their respective medians,
    computed from the training dataset.

    >>> step = ml.ImputeMedian(ml.numeric())
    """

    def _stat(self, col: ir.Column) -> ir.Scalar:
        if not isinstance(col, ir.NumericColumn):
            raise ValueError(
                f"Cannot compute median of {col.get_name()} - "
                "this column is not numeric"
            )
        return col.median()


class ImputeMode(_BaseImpute):
    """A step for replacing NULL values in select columns with their
    respective modes in the training set.

    Parameters
    ----------
    inputs
        A selection of columns to impute.

    Examples
    --------
    >>> import ibisml as ml

    Replace NULL values in all numeric columns with their respective modes,
    computed from the training dataset.

    >>> step = ml.ImputeMode(ml.numeric())
    """

    def _stat(self, col: ir.Column) -> ir.Scalar:
        return col.mode()
