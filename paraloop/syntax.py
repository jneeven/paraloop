import ast
import itertools
import random
from pathlib import Path
from typing import Dict, List

from paraloop.variable import Variable


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
        self.variable_names = set(
            [key for key, value in self.scope.items() if isinstance(value, Variable)]
        )

        # This is used to distinguish the loop we're trying to convert from any inner
        # for loops that it may be wrapping.
        self._in_nested_for = False

    def build_loop_function(self):
        """Creates an executable function that will be called for each iteration in the
        for-loop."""
        function_tree = self.visit(ast.parse(self.source))
        # print(ast.unparse(function_tree))
        # print(ast.dump(function_tree, indent=4))

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
            self._in_nested_for = True
            node = self.generic_visit(node)
            self._in_nested_for = False
            return node

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
        return self.generic_visit(new_node)

    def visit_Assign(self, node: ast.Assign):
        if len(node.targets) > 1:
            for target in node.targets:
                if hasattr(target, "id") and target.id in self.variable_names:
                    raise TypeError(
                        "You cannot assign to multiple paraloop Variables in a single statement. "
                        "Try assigning one at a time."
                    )
            return self.generic_visit(node)

        if hasattr(node.targets[0], "id") and node.targets[0].id in self.variable_names:
            new_node = ast.Expr(
                ast.Call(
                    func=ast.Attribute(
                        ast.Name(id=node.targets[0].id, ctx=ast.Load()),
                        "assign",
                        ast.Load(),
                    ),
                    args=[node.value],
                    keywords=[],
                ),
            )
            ast.fix_missing_locations(new_node)
            return new_node

        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if hasattr(node.target, "id") and node.target.id in self.variable_names:
            raise TypeError(
                "Your loop contains an annotated assign to a paraloop Variable "
                f"on line {node.lineno - 1}, that is not supported!"
            )
        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        if hasattr(node.target, "id") and node.target.id in self.variable_names:
            new_node = ast.Expr(
                ast.Call(
                    func=ast.Attribute(
                        ast.Name(id=node.target.id, ctx=ast.Load()),
                        "assign",
                        ast.Load(),
                    ),
                    args=[
                        ast.BinOp(
                            left=ast.Name(id=node.target.id, ctx=ast.Load()),
                            op=node.op,
                            right=node.value,
                        )
                    ],
                    keywords=[],
                ),
            )
            ast.fix_missing_locations(new_node)
            return new_node
        return self.generic_visit(node)

    def visit_Continue(self, node: ast.Continue):
        if self._in_nested_for:
            return node

        new_node = ast.Return(value=ast.Constant(value=None))
        ast.fix_missing_locations(new_node)
        return new_node
