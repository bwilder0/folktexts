import logging
from typing import Callable

from .qa_interface import QAInterface, MultipleChoiceQA


class ColumnToText:
    """Maps a single column's values to natural text."""

    def __init__(
            self,
            name: str,
            short_description: str,
            value_map: dict[object, str] | Callable = None,
            question: QAInterface = None,
            connector_verb: str = "is",
            missing_value_fill: str = "N/A",
        ):
        """Constructs a `ColumnToText` object.

        Parameters
        ----------
        name : str
            The column's name.
        short_description : str
            A short description of the column to be used before different
            values. For example, short_description="yearly income" will result
            in "The yearly income is [...]".
        value_map : dict[int | str, str] | Callable, optional
            A map between column values and their textual meaning. If not
            provided, will try to infer a mapping from the `question`.
        question : QAInterface, optional
            A question associated with the column. If not provided, will try to
            infer a multiple-choice question from the `value_map`.
        connector_verb : str, optional
            Which verb to use when connecting the column's description to its
            value; by default "is".
        missing_value_fill : str, optional
            The value to use when the column's value is not found in the
            `value_map`, by default "N/A".
        """
        self._name = name
        self._short_description = short_description
        self._value_map = value_map
        self._question = question
        self._connector_verb = connector_verb
        self._missing_value_fill = missing_value_fill

        # If a `question` was provided and `value_map` was not
        # > infer `value_map` from question (`value_map` is required for `__getitem__`)
        if self._question is not None and self._value_map is None:
            if isinstance(self._question, MultipleChoiceQA):
                self._value_map = self._question.get_value_to_text_map()
            else:
                raise ValueError(
                    f"Cannot infer `ColumnToText` value map from the provided question; "
                    f"Must explicitly provide a `value_map` for column {self.name}.")

        # If `value_map` was provided and `question` was not
        # > infer `question` from value map (if possible)
        elif self._value_map is not None and self._question is None:
            if isinstance(self._value_map, dict):
                self._question = MultipleChoiceQA.create_question_from_value_map(
                    column=self.name,
                    value_map=self._value_map,
                    attribute=self.short_description,
                )

        # Else, warn if both were provided (as they may use inconsistent value maps)
        elif self._value_map is not None and self._question is not None:
            logging.warning(
                f"Got both `value_map` and `question` for column '{self.name}'. "
                f"Please make sure value mappings are consistent.")

        # Else, raise an error if neither were provided
        else:
            raise ValueError(
                f"Must provide either a `value_map` or a `question` for column "
                f"'{self.name}' but neither was provided.")

    @property
    def name(self) -> str:
        return self._name

    @property
    def short_description(self) -> str:
        return self._short_description

    @property
    def question(self) -> QAInterface:
        if self._question is None:
            logging.error(f"No question provided for column '{self.name}'.")
        return self._question

    @property
    def value_map(self) -> Callable:
        """Returns the value map function for this column."""
        if callable(self._value_map):
            return self._value_map
        elif isinstance(self._value_map, dict):
            def _helper_func(value: object) -> str:
                if value not in self._value_map:
                    logging.error(f"Could not find value '{value}' in value map for column '{self.name}'.")
                return self._value_map.get(value, self._missing_value_fill)
            return _helper_func
        else:
            raise ValueError(
                f"Invalid value map type '{type(self._value_map)}' "
                f"for column '{self.name}'.")

    def __getitem__(self, value: object) -> str:
        """Returns the textual representation of the given data value."""
        return self.value_map(value)

    def get_text(self, value: object) -> str:
        return f"The {self.short_description} {self._connector_verb} {self[value]}."
