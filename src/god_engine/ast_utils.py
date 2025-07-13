import ast


class AstRefactorer(ast.NodeTransformer):
    """
    A class to perform AST-based refactoring for specific Pylint issues.
    """
    def __init__(self, max_branches=12, max_statements=50):
        self.max_branches = max_branches
        self.max_statements = max_statements
        self.helper_methods = []

    def _count_branches(self, node):
        """Recursively count branches in a node."""
        count = 0
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            count += 1
        if isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
        for child in ast.iter_child_nodes(node):
            count += self._count_branches(child)
        return count

    def visit_FunctionDef(self, node):
        """
        Visits a function definition to check for too many branches or statements.
        """
        branches = self._count_branches(node)
        statements = len(node.body)

        if branches > self.max_branches:
            return self._refactor_complex_function(node, "branches")
        if statements > self.max_statements:
            return self._refactor_complex_function(node, "statements")

        return self.generic_visit(node)

    def _refactor_complex_function(self, node: ast.FunctionDef, reason: str):
        """
        Extracts a part of a complex function into a helper method.
        """
        # For now, we'll do a simple extraction of the second half of the
        # function body. A more sophisticated approach would analyze the logic
        # to find a cohesive block.
        if len(node.body) < 2:
            return node

        split_point = len(node.body) // 2
        body_to_extract: list[ast.stmt] = node.body[split_point:]
        original_body: list[ast.stmt] = node.body[:split_point]

        helper_method_name = f"_helper_{node.name}_{reason}"

        # Create the helper method
        helper_method = ast.FunctionDef(
            name=helper_method_name,
            args=node.args,
            body=body_to_extract,
            decorator_list=[],
            returns=None,
            type_comment=None,
            type_params=[]
        )
        self.helper_methods.append(helper_method)

        # Modify the original function to call the helper
        call_to_helper = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='self', ctx=ast.Load()),
                    attr=helper_method_name,
                    ctx=ast.Load()
                ),
                args=[
                    ast.Name(id=arg.arg, ctx=ast.Load()) for arg in node.args.args
                ],
                keywords=[]
            )
        )
        node.body = original_body + [call_to_helper]

        return node

    def visit_If(self, node):
        """
        Transforms 'if-else-return' structures into a simpler 'return'.
        Example:
            if condition:
                return True
            else:
                return False
        Becomes:
            return condition
        """
        # Ensure the node has an 'else' block and it's not an 'elif'
        if not node.orelse or isinstance(node.orelse[0], ast.If):
            return self.generic_visit(node)

        # Check if the 'if' block ends with a return statement
        if_returns = isinstance(node.body[-1], ast.Return)

        # Check if the 'else' block contains only a return statement
        else_returns = len(node.orelse) == 1 and isinstance(
            node.orelse[0], ast.Return
        )

        if if_returns and else_returns:
            # This is a simple if/else with return statements in both branches.
            # We can simplify this to a single return with a conditional
            # expression.
            return_if_true = node.body[-1]
            return_if_false = node.orelse[0]

            if isinstance(return_if_true, ast.Return) and isinstance(
                return_if_false, ast.Return
            ):
                if return_if_true.value and return_if_false.value:
                    new_return = ast.Return(
                        value=ast.IfExp(
                            test=node.test,
                            body=return_if_true.value,
                            orelse=return_if_false.value
                        )
                    )
                    # Copy line number and column offset for debugging
                    ast.copy_location(new_return, node)
                    return new_return

        return self.generic_visit(node)
