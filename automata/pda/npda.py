#!/usr/bin/env python3
"""Classes and methods for working with nondeterministic pushdown automata."""

from typing import AbstractSet, Generator, Mapping, Set, Tuple, Union

import automata.base.exceptions as exceptions
import automata.pda.pda as pda
from automata.pda.configuration import PDAConfiguration
from automata.pda.stack import PDAStack

NPDAStateT = pda.PDAStateT

NPDAPathT = Mapping[
    str,
    Mapping[str, AbstractSet[Tuple[NPDAStateT, Union[str, Tuple[str, ...]]]]],
]
NPDATransitionsT = Mapping[NPDAStateT, NPDAPathT]


class NPDA(pda.PDA):
    """A nondeterministic pushdown automaton."""

    __slots__ = (
        "states",
        "input_symbols",
        "stack_symbols",
        "transitions",
        "initial_state",
        "initial_stack_symbol",
        "final_states",
        "acceptance_mode",
    )

    def __init__(
        self,
        *,
        states: AbstractSet[NPDAStateT],
        input_symbols: AbstractSet[str],
        stack_symbols: AbstractSet[str],
        transitions: NPDATransitionsT,
        initial_state: NPDAStateT,
        initial_stack_symbol: str,
        final_states: AbstractSet[NPDAStateT],
        acceptance_mode: pda.PDAAcceptanceModeT = "both",
    ) -> None:
        """Initialize a complete NPDA."""
        super().__init__(
            states=states,
            input_symbols=input_symbols,
            stack_symbols=stack_symbols,
            transitions=transitions,
            initial_state=initial_state,
            initial_stack_symbol=initial_stack_symbol,
            final_states=final_states,
            acceptance_mode=acceptance_mode,
        )

    def _validate_transition_invalid_symbols(
        self, start_state: NPDAStateT, paths: NPDATransitionsT
    ) -> None:
        """Raise an error if transition symbols are invalid."""
        for input_symbol, symbol_paths in paths.items():
            self._validate_transition_invalid_input_symbols(start_state, input_symbol)
            for stack_symbol in symbol_paths:
                self._validate_transition_invalid_stack_symbols(
                    start_state, stack_symbol
                )

    def _get_transitions(
        self, state: NPDAStateT, input_symbol: str, stack_symbol: str
    ) -> Set[Tuple[str, NPDAStateT, str]]:
        """Get the transition tuples for the given state and symbols."""
        transitions = set()
        if (
            state in self.transitions
            and input_symbol in self.transitions[state]
            and stack_symbol in self.transitions[state][input_symbol]
        ):
            for dest_state, new_stack_top in self.transitions[state][input_symbol][stack_symbol]:
                transitions.add((input_symbol, dest_state, new_stack_top))
        return transitions

    def _get_next_configurations(
        self, old_config: PDAConfiguration
    ) -> Set[PDAConfiguration]:
        """Advance to the next configurations."""
        transitions: Set[Tuple[str, NPDAStateT, str]] = set()
        if old_config.remaining_input:
            transitions.update(
                self._get_transitions(
                    old_config.state,
                    old_config.remaining_input[0],
                    old_config.stack.top(),
                )
            )
        transitions.update(
            self._get_transitions(old_config.state, "", old_config.stack.top())
        )
        new_configs = set()
        for input_symbol, new_state, new_stack_top in transitions:  # type: ignore
            remaining_input = old_config.remaining_input
            if input_symbol:
                remaining_input = remaining_input[1:]
            new_config = PDAConfiguration(
                new_state,
                remaining_input,
                self._replace_stack_top(old_config.stack, new_stack_top),
            )
            new_configs.add(new_config)
        return new_configs

    def read_input_stepwise(
        self, input_str: str
    ) -> Generator[Set[PDAConfiguration], None, None]:
        """
        Check if the given string is accepted by this NPDA.

        Yield the NPDA's current configurations at each step.
        """
        current_configurations = set()
        current_configurations.add(
            PDAConfiguration(
                self.initial_state, input_str, PDAStack([self.initial_stack_symbol])
            )
        )

        yield current_configurations

        while current_configurations:
            new_configurations = set()
            for config in current_configurations:
                if self._has_accepted(config):
                    # One accepting configuration is enough.
                    return
                if config.remaining_input:
                    new_configurations.update(self._get_next_configurations(config))
                elif self._has_lambda_transition(config.state, config.stack.top()):
                    new_configurations.update(self._get_next_configurations(config))
            current_configurations = new_configurations
            yield current_configurations

        raise exceptions.RejectionException(
            "the NPDA did not reach an accepting configuration"
        )

    def read_partial_input_stepwise(
        self, input_str: str
    ) -> Generator[Set[PDAConfiguration], None, None]:
        """
        Check if the given string is accepted by this NPDA.

        Yield the NPDA's current configurations at each step.
        """
        current_configurations = set()
        current_configurations.add(
            PDAConfiguration(
                self.initial_state, input_str, PDAStack([self.initial_stack_symbol])
            )
        )

        # yield current_configurations

        # partial_accepting_configurations = set()

        while current_configurations:
            new_configurations = set()
            for config in current_configurations:
                if not config.remaining_input:
                    # at least one of the configurations has no remaining input
                    # partial_accepting_configurations.add(config)
                    return config
                if config.remaining_input:
                    new_configurations.update(self._get_next_configurations(config))
                elif self._has_lambda_transition(config.state, config.stack.top()):
                    new_configurations.update(self._get_next_configurations(config))
            current_configurations = new_configurations
            # yield current_configurations

        raise exceptions.RejectionException(
            "the NPDA did not reach an accepting configuration"
        )
    
    
    def get_next_possible_char(self,
            current_configurations: Set[PDAConfiguration]
    ) -> Generator[Set[PDAConfiguration], None, None]:
        """
        Return the next possible char for the current configuration.
        A char is possible if it can be accpeted by the current configuration.
        """

        next_possible_char = set()

        while current_configurations:
            new_configurations = set()
            for config in current_configurations:
                next_possible_char.update(self._get_next_possible_char(config))
                if self._has_lambda_transition(config.state, config.stack.top()):
                    new_configurations.update(self._get_next_configurations(config))
            current_configurations = new_configurations
            # yield current_configurations

        return next_possible_char
    
    def _get_next_possible_char(self, current_config: PDAConfiguration) -> Set[str]:
        """
        Return the next possible char at the current configuration without considering the lambda transition.
        Adapted from the _get_next_configurations method.
        """
        
        next_possible_char = set()
        # state_compliant_transitions = self.transitions.get(current_config.state, {})
        # for 
        
        if current_config.state in self.transitions:
            transitions = self.transitions[current_config.state]
            # loop through all the input symbols in the transition
            for input_symbol in transitions:
                # don't consider lambda transitions here
                if input_symbol == "":
                    continue
                # check if the current config's stack top is in the transition's stack
                if current_config.stack.top() in transitions[input_symbol]:
                    next_possible_char.add(input_symbol)

        return next_possible_char
                    
                    
        
        
        
        
        
        """Advance to the next configurations."""
        transitions: Set[Tuple[str, NPDAStateT, str]] = set()
        if old_config.remaining_input:
            transitions.update(
                self._get_transitions(
                    old_config.state,
                    old_config.remaining_input[0],
                    old_config.stack.top(),
                )
            )
        transitions.update(
            self._get_transitions(old_config.state, "", old_config.stack.top())
        )
        new_configs = set()
        for input_symbol, new_state, new_stack_top in transitions:  # type: ignore
            remaining_input = old_config.remaining_input
            if input_symbol:
                remaining_input = remaining_input[1:]
            new_config = PDAConfiguration(
                new_state,
                remaining_input,
                self._replace_stack_top(old_config.stack, new_stack_top),
            )
            new_configs.add(new_config)
        return new_configs
    
    """
            transitions = set()
        if (
            state in self.transitions
            and input_symbol in self.transitions[state]
            and stack_symbol in self.transitions[state][input_symbol]
        ):
            for dest_state, new_stack_top in self.transitions[state][input_symbol][stack_symbol]:
                transitions.add((input_symbol, dest_state, new_stack_top))
        return transitions
    """
        
        
        
        
        
