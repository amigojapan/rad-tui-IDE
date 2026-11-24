"""Translate the small, statically typed callback subset of RAD-TUI projects."""

import ast


class CallbackTranslationError(ValueError):
    """A Python callback cannot be represented by the native C++ runtime."""


_CONTROL_FIELDS = {
    'caption': 'str', 'value': 'int', 'x': 'int', 'y': 'int',
    'w': 'int', 'h': 'int', 'interval': 'int', 'bg_color': 'int', 'fg_color': 'int',
    'custom_bg': 'int', 'list_index': 'int', 'scroll_offset': 'int',
    'scroll_x': 'int', 'scroll_y': 'int', 'editable': 'bool',
}


def _cpp_string(value):
    return '"' + ''.join('\\x%02x' % byte for byte in value.encode('utf-8')) + '"'


def _source(node):
    return ast.unparse(node) if hasattr(ast, 'unparse') else ast.dump(node)


class _Translator:
    def __init__(self, project):
        self.project = project
        self.controls = {item.get('name_id'): index for index, item in
                         enumerate(project.get('controls', []))}
        self.functions = {}
        self.location = ''

    def fail(self, node, reason):
        line = getattr(node, 'lineno', 1)
        raise CallbackTranslationError(f'{self.location}, line {line}: {reason}')

    def collect(self, label, source):
        self.location = label
        if not source or not source.strip():
            return
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise CallbackTranslationError(
                f'{label}, line {exc.lineno}: invalid Python syntax: {exc.msg}') from exc
        for node in tree.body:
            if isinstance(node, ast.Pass):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            if not isinstance(node, ast.FunctionDef):
                self.fail(node, f'unsupported top-level {type(node).__name__}; use no-argument callback functions')
            if (node.decorator_list or node.returns or getattr(node, 'type_params', None) or
                    node.args.posonlyargs or node.args.args or node.args.kwonlyargs or
                    node.args.vararg or node.args.kwarg or node.args.defaults or
                    node.args.kw_defaults):
                self.fail(node, f'callback {node.name} must have no arguments, decorators, or annotations')
            self.functions[node.name] = (label, node)

    def expr(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return 'std::string(' + _cpp_string(node.value) + ')', 'str'
            if isinstance(node.value, bool):
                return ('true' if node.value else 'false'), 'bool'
            if isinstance(node.value, int):
                return str(node.value), 'int'
            self.fail(node, f'unsupported literal {type(node.value).__name__}')
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            name = node.value.id
            if name not in self.controls:
                self.fail(node, f'unknown control {name!r}')
            kind = _CONTROL_FIELDS.get(node.attr)
            if kind is None:
                self.fail(node, f'unsupported control property {name}.{node.attr}')
            return f'controls[{self.controls[name]}].{node.attr}', kind
        if isinstance(node, ast.UnaryOp):
            value, kind = self.expr(node.operand)
            if isinstance(node.op, ast.Not) and kind in ('bool', 'int'):
                return f'(!({value}))', 'bool'
            if isinstance(node.op, ast.USub) and kind == 'int':
                return f'(-({value}))', 'int'
        if isinstance(node, ast.BinOp):
            left, left_kind = self.expr(node.left)
            right, right_kind = self.expr(node.right)
            if isinstance(node.op, ast.Add) and left_kind == right_kind and left_kind in ('str', 'int'):
                return f'({left} + {right})', left_kind
            if isinstance(node.op, ast.Sub) and left_kind == right_kind == 'int':
                return f'({left} - {right})', 'int'
        if isinstance(node, ast.BoolOp):
            values = [self.expr(value) for value in node.values]
            if all(kind in ('bool', 'int') for _, kind in values):
                op = ' && ' if isinstance(node.op, ast.And) else ' || '
                return '(' + op.join(value for value, _ in values) + ')', 'bool'
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, left_kind = self.expr(node.left)
            right, right_kind = self.expr(node.comparators[0])
            op = node.ops[0]
            signs = {ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
                     ast.Gt: '>', ast.GtE: '>='}
            if (left_kind == right_kind or {left_kind, right_kind} == {'bool', 'int'}) and type(op) in signs:
                return f'({left} {signs[type(op)]} {right})', 'bool'
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            if node.func.id == 'str' and len(node.args) == 1:
                value, kind = self.expr(node.args[0])
                if kind == 'int':
                    return f'std::to_string({value})', 'str'
        self.fail(node, f'unsupported expression {_source(node)!r}')

    def statement(self, node, indent='    '):
        if isinstance(node, ast.Pass):
            return ''
        if isinstance(node, ast.Return) and node.value is None:
            return indent + 'return;\n'
        if isinstance(node, ast.If):
            test, kind = self.expr(node.test)
            if kind not in ('bool', 'int'):
                self.fail(node.test, 'if condition must be boolean or integer')
            body = ''.join(self.statement(item, indent + '    ') for item in node.body)
            result = indent + f'if ({test}) {{\n' + body + indent + '}'
            if node.orelse:
                result += ' else {\n' + ''.join(self.statement(item, indent + '    ') for item in node.orelse) + indent + '}'
            return result + '\n'
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if len(targets) != 1 or not isinstance(targets[0], ast.Attribute):
                self.fail(node, 'only a single control property can be assigned')
            target, target_kind = self.expr(targets[0])
            value, value_kind = self.expr(node.value)
            if target_kind != value_kind and not (target_kind == 'int' and value_kind == 'bool'):
                self.fail(node, f'assignment type mismatch: {target_kind} and {value_kind}')
            if isinstance(node, ast.AugAssign):
                if not isinstance(node.op, (ast.Add, ast.Sub)) or target_kind not in ('int', 'str'):
                    self.fail(node, 'unsupported compound assignment')
                op = '+=' if isinstance(node.op, ast.Add) else '-='
                if op == '-=' and target_kind == 'str':
                    self.fail(node, 'strings cannot be subtracted')
            else:
                op = '='
            return indent + f'{target} {op} {value};\n'
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if not isinstance(call.func, ast.Name) or call.keywords:
                self.fail(node, f'unsupported call {_source(call)!r}')
            name = call.func.id
            if name == 'msgbox' and len(call.args) == 1:
                message, kind = self.expr(call.args[0])
                if kind != 'str':
                    self.fail(call, 'msgbox expects a string')
                return indent + f'native_msgbox({message});\n'
            if name == 'END' and not call.args:
                return indent + 'running = false;\n'
            if name in self.functions and not call.args:
                return indent + f'callback_{self.names[name]}();\n'
            self.fail(call, f'unsupported call {_source(call)!r}')
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return ''
        self.fail(node, f'unsupported statement {type(node).__name__}: {_source(node)!r}')

    def compile(self):
        self.collect('form code', self.project.get('code', ''))
        for control in self.project.get('controls', []):
            self.collect(f"control {control.get('name_id', '<unnamed>')}", control.get('code', ''))

        def menus(items):
            for item in items:
                self.collect(f"menu {item.get('name', item.get('label', '<unnamed>'))}", item.get('code', ''))
                menus(item.get('sub', []))

        menus(self.project.get('menus', []))
        control_types = {item.get('name_id'): item.get('tool_type')
                         for item in self.project.get('controls', [])}
        for name, (label, function) in self.functions.items():
            active = any(not isinstance(node, ast.Pass) and not (
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and
                isinstance(node.value.value, str)) for node in function.body)
            if not active:
                continue
            self.location = f'{label}, function {name}'
            if name in ('on_form_key',) or name.startswith(('on_mouse_', 'on_double_click_')):
                self.fail(function, f'event handler {name} is not supported by the native event loop')
            checks = (
                ('on_click_', lambda kind: kind not in (None, 14)),
                ('on_change_', lambda kind: kind in (8, 13, 15)),
                ('on_enter_', lambda kind: kind in (10, 13)),
                ('on_tick_', lambda kind: kind == 14),
                ('on_right_click_', lambda kind: kind is not None),
                ('button_down_', lambda kind: kind == 3),
                ('on_button_up_', lambda kind: kind == 3),
            )
            for prefix, allowed in checks:
                if name.startswith(prefix):
                    control_name = name[len(prefix):]
                    if not allowed(control_types.get(control_name)):
                        self.fail(function, f'event handler {name} has no supported target control')
                    break
        self.names = {name: index for index, name in enumerate(self.functions)}
        result = []
        for name, index in self.names.items():
            result.append(f'static void callback_{index}();')
        for name, (label, function) in self.functions.items():
            self.location = f'{label}, function {name}'
            body = ''.join(self.statement(node) for node in function.body)
            result.append(f'static void callback_{self.names[name]}() {{\n{body}}}')
        result.append('static void dispatch(const std::string& name) {\n    (void)name;')
        for name, index in self.names.items():
            result.append(f'    if (name == {_cpp_string(name)}) {{ callback_{index}(); return; }}')
        result.append('}')
        return '\n'.join(result)


def compile_callbacks(project):
    """Return native callback functions, or report the first unsupported source line."""
    return _Translator(project).compile()
