#!/bin/bash

# Script to clean up test files and remove individual database setups

# List of test files that need to be updated
files=(
    "test_audit_api.py"
    "test_money_moves_api.py"
    "test_exports_api.py"
    "test_models_extended.py"
    "test_audit_service.py"
    "test_csv_export_service.py"
    "test_integration_workflows.py"
    "test_models.py"
    "test_services.py"
)

cd /home/martin/git/coffee_fund_app/backend/app/tests

for file in "${files[@]}"
do
    if [ -f "$file" ]; then
        echo "Updating $file..."
        
        # Create a backup
        cp "$file" "$file.backup"
        
        # Remove the database setup section (from import FastAPI to @pytest.fixture)
        # and replace with simple imports
        python3 << EOF
import re

# Read file
with open('$file', 'r') as f:
    content = f.read()

# Pattern to match the database setup section
pattern = r'from fastapi\.testclient import TestClient.*?@pytest\.fixture'

# Find the section and replace it with simple imports
match = re.search(pattern, content, re.DOTALL)
if match:
    # Extract just the imports we need
    import_section = []
    
    # Always keep these imports
    if 'import pytest' not in content:
        import_section.append('import pytest')
    
    # Keep other necessary imports
    if 'from uuid import uuid4' in content:
        import_section.append('from uuid import uuid4')
    
    # Look for model imports
    if 'from app.models' in content:
        model_imports = re.findall(r'from app\.models[^\\n]*', content)
        import_section.extend(model_imports)
    
    # Look for service imports
    if 'from app.services' in content:
        service_imports = re.findall(r'from app\.services[^\\n]*', content)
        import_section.extend(service_imports)
        
    # Look for enum imports
    if 'from app.core.enums' in content:
        enum_imports = re.findall(r'from app\.core\.enums[^\\n]*', content)
        import_section.extend(enum_imports)
    
    # Replace the database setup with clean imports
    replacement = '\\n'.join(import_section) + '\\n\\n\\n@pytest.fixture'
    
    new_content = content.replace(match.group(0), replacement)
    
    with open('$file', 'w') as f:
        f.write(new_content)
        
    print(f"Updated {file}")
else:
    print(f"No database setup found in {file}")
EOF
    fi
done

echo "All test files updated!"