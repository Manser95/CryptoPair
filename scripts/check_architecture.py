#!/usr/bin/env python
"""Architecture validation script"""

import os
import ast
import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def analyze_imports(file_path):
    """Analyze imports in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return []


def check_layer_violations():
    """Check for architectural violations"""
    violations = []
    
    # Define layers
    layers = {
        'presentation': 'src/presentation',
        'services': 'src/services', 
        'data_access': 'src/data_access',
        'shared': 'src/shared'
    }
    
    # Valid dependencies (layer -> allowed dependencies)
    allowed_deps = {
        'presentation': ['services', 'shared'],
        'services': ['data_access', 'shared'],
        'data_access': ['shared'],
        'shared': []
    }
    
    for layer_name, layer_path in layers.items():
        layer_dir = Path(layer_path)
        if layer_dir.exists():
            for py_file in layer_dir.rglob('*.py'):
                if py_file.name == "__init__.py":
                    continue
                    
                imports = analyze_imports(py_file)
                
                for imp in imports:
                    if imp.startswith('src.'):
                        # Extract layer from import
                        parts = imp.split('.')
                        if len(parts) >= 2:
                            imported_layer = parts[1]
                            
                            # Check if this is a valid dependency
                            if imported_layer in layers and imported_layer not in allowed_deps[layer_name]:
                                violations.append({
                                    'file': str(py_file),
                                    'layer': layer_name,
                                    'violates': imported_layer,
                                    'import': imp
                                })
    
    return violations


def main():
    print("🏗️  Architecture Analysis")
    print("=" * 50)
    
    # Check layer violations
    violations = check_layer_violations()
    
    if violations:
        print("❌ Architecture violations found:")
        for v in violations:
            print(f"  {v['file']}")
            print(f"    Layer '{v['layer']}' should not import from '{v['violates']}'")
            print(f"    Import: {v['import']}")
            print()
    else:
        print("✅ No architecture violations found!")
    
    # Count files by layer
    layers = {
        'Presentation': len(list(Path('src/presentation').rglob('*.py'))),
        'Services': len(list(Path('src/services').rglob('*.py'))),
        'Data Access': len(list(Path('src/data_access').rglob('*.py'))),
        'Shared': len(list(Path('src/shared').rglob('*.py')))
    }
    
    print("\n📊 Layer Distribution:")
    for layer, count in layers.items():
        print(f"  {layer}: {count} files")
    
    print("\n✅ Architecture analysis complete!")


if __name__ == "__main__":
    main()