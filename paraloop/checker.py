import ast


def reverse_iter_fields(node):
    """Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields`` that
    is present on *node*.

    Same as ast.iter_fields, but traverses the fields from right to left.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


def reverse_iter_child_nodes(node):
    """Yield all direct child nodes of *node*, that is, all fields that are nodes and
    all items of fields that are lists of nodes.

    Same as ast.iter_child_nodes, but traverses the fields from right to left.
    """
    for name, field in reverse_iter_fields(node):
        if isinstance(field, ast.AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, ast.AST):
                    yield item


def recursive_check_variables(node, local_vars, depth=0):
    print(node, node.lineno, depth)
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        recursive_check_variables(node.value, local_vars, depth=depth + 1)
        for target in node.targets:
            assert isinstance(target.ctx, ast.Store)
            local_vars.add(target.id)
    else:
        # recursive_check_variables(node.)
        print(node)

    # for child in reverse_iter_child_nodes(node):
    #     # if hasattr(child, "lineno"):
    #     #     print(child, child.lineno)
    #     if isinstance(child, ast.Assign):
    #         print(child)
    #     if isinstance(child, ast.Name):
    #         if isinstance(child.ctx, (ast.Store, ast.AugStore)):
    #             local_vars.add(child.id)
    #         elif isinstance(child.ctx, (ast.Load, ast.AugLoad)):
    #             print(child.id, child.id in local_vars)
    #         else:
    #             raise ValueError("What the hell?")

    #     recursive_check_variables(child, local_vars)
