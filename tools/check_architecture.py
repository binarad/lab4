"""Static verification; intentionally separate from the isolated unit test suite."""
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
allowed = {
    'Domain': {'src.Domain'},
    'Application': {'src.Domain', 'src.Application'},
    'Infrastructure': {'src.Domain', 'src.Application', 'src.Infrastructure'},
    'WebAPI': {'src.Domain', 'src.Application', 'src.Infrastructure', 'src.WebAPI'},
}
errors = []
count = 0
for layer, permitted in allowed.items():
    for path in sorted((root / 'src' / layer).glob('*.py')):
        count += 1
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            imports = []
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imports = [node.module or '']
            for name in imports:
                if name.startswith('src.') and '.'.join(name.split('.')[:2]) not in permitted:
                    errors.append(f'{path.relative_to(root)}:{node.lineno}: forbidden {name}')
                if layer == 'Domain' and not name.startswith('src.'):
                    if name.split('.')[0] not in {'dataclasses', 'datetime', 'enum', 'uuid', 'typing', 'decimal', 'math'}:
                        errors.append(f'Domain external import: {name}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: dependency rule verified for {count} Python files.')
print('Domain imports only its own types and Python standard-library value types.')
