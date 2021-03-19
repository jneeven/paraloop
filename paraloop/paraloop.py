import ast
import inspect
import itertools
import random
from pathlib import Path
from typing import Any, Dict, List


class Variable:
    """Wraps any kind of variable and specifies how to aggregate it over the different
    processes."""

    __paraloop_attributes__ = set(["wrapped"])

    def __init__(self, wrapped: Any) -> None:
        self.wrapped = wrapped

    def __getattribute__(self, name: str) -> Any:
        """Wrap all non-paraloop attributes automatically."""
        if name == "__paraloop_attributes__" or name in self.__paraloop_attributes__:
            return super().__getattribute__(name)
        return self.wrapped.__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Wrap all non-paraloop attributes automatically."""
        if name == "__paraloop_attributes__" or name in self.__paraloop_attributes__:
            return super().__setattr__(name, value)
        return self.wrapped.__setattr__(name, value)


class LoopFinder(ast.NodeVisitor):
    """Obtains the source code of a for-loop given a source file and its line number in
    that file.

    Also detects the loop targets, i.e. `i` in `for i in range(10)`, and makes sure
    there is only one of them (multi-target loops are unsupported for now)
    """

    def __init__(self, lineno: int, filename: str):
        self.lineno = lineno
        self.filename = filename

        self.found_node = None

    def find_loop(self):
        # Read the source code, construct an AST and traverse it
        source = Path(self.filename).read_text()
        self.visit(ast.parse(source, filename=self.filename))

        if not self.found_node:
            raise ValueError(
                f"Did not find for loop at line {self.lineno} of file {self.filename}!"
            )

        # Obtain the source code of only this loop and identify its target variables
        loop_source = ast.get_source_segment(source, self.found_node)
        targets = self._recursive_list_targets(self.found_node.target)

        if len(targets) > 1:
            raise ValueError(
                "Wrapping loops with multiple target values is currently not supported! "
                "Try unwrapping the target inside the loop, e.g.\n```\n"
                "for x in ParaLoop(iterable):\n"
                "\telem1, elem2 = x\n```"
            )

        return loop_source

    def visit_For(self, node: ast.For):
        if node.lineno != self.lineno:
            return self.generic_visit(node)

        self.found_node = node

    def _recursive_list_targets(self, node) -> List:
        """Find the names of all targets of this for loop, e.g. `for x, y in iterable`
        will return `['x', 'y']`."""
        targets = []
        if isinstance(node, ast.Name):
            targets.append(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            assert isinstance(node.ctx, ast.Store)
            for child in node.elts:
                targets.extend(self._recursive_list_targets(child))
        return targets


class LoopTransformer(ast.NodeTransformer):
    """Given the source code of a for-loop and its target- and local variables, create
    an executable function that can be called for each iteration of the loop."""

    def __init__(self, source: str, globals: Dict, locals: Dict):
        self.source = source
        self.scope = {
            key: value
            for key, value in itertools.chain(globals.items(), locals.items())
        }

    def build_loop_function(self):
        """Creates an executable function that will be called for each iteration in the
        for-loop."""
        function_tree = self.visit(ast.parse(self.source))
        function_name = function_tree.body[0].name
        assert function_name not in self.scope

        # Parse the string and insert it into the scope
        function = compile(function_tree, filename="<wrapped_loop>", mode="exec")
        exec(function, self.scope)

        # Retrieve the created function from the scope
        function = self.scope[function_name]
        return function

    def visit_For(self, node: ast.For):
        """Converts the for-loop into a function with a random name."""
        # We only convert the outermost for-loop.
        if node.lineno != 1:
            return self.generic_visit(node)

        # For now, we only support a single target.
        target = node.target
        assert isinstance(target, ast.Name)

        args = ast.arguments(
            posonlyargs=[ast.arg(arg=target.id)],
            args=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        )
        new_node = ast.FunctionDef(
            name=f"loop_{random.randint(0, 10000)}_iteration",
            args=args,
            body=node.body,
            decorator_list=[],
        )

        ast.fix_missing_locations(new_node)
        print(ast.dump(new_node, indent=4))

        return self.generic_visit(new_node)


class ParaLoop:
    """Wraps an iterable and executes its iterations in parallel over multiple
    processes."""

    def __init__(self, iterable, length=None):
        self.iterable = iter(iterable)
        self.length = length or len(iterable)
        self.index = 0

    def __iter__(self):
        # Find the source code of the calling loop and transform it into a function
        caller = inspect.stack()[1]
        loop_source = LoopFinder(caller.lineno, filename=caller.filename).find_loop()
        function = LoopTransformer(
            loop_source, caller.frame.f_globals, caller.frame.f_locals
        ).build_loop_function()

        function(1)
        function(2)

        # TODO: perform initialization of the processes
        return self

    def __next__(self):
        # return next(self.iterable)
        raise StopIteration
