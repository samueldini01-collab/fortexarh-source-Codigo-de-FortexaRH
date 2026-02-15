"""
Refactoring script: Remove init_router pattern from all route files.
Replace with direct imports from config and utils.auth.
"""
import re
import os

ROUTES_DIR = "/app/backend/routes"

def refactor_file(filepath):
    """Refactor a single route file to remove init_router pattern."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    filename = os.path.basename(filepath)
    
    # Skip __init__.py
    if filename == "__init__.py":
        return False
    
    # Track what we need to add to imports
    needs_db_import = False
    needs_auth_import = False
    needs_config_imports = []
    needs_email_imports = []
    
    # --- Step 1: Detect what this file needs ---
    
    # Check if file uses db
    if re.search(r'^db\s*=\s*None', content, re.MULTILINE):
        needs_db_import = True
    
    # Check if file has a local get_current_user wrapper
    has_local_auth = bool(re.search(r'^_get_current_user_func', content, re.MULTILINE))
    if has_local_auth:
        needs_auth_import = True
    
    # Special: subscriptions.py needs extra config imports
    if filename == "subscriptions.py":
        needs_config_imports = ["SUBSCRIPTION_PLANS", "FEATURE_ACCESS", "ADDITIONAL_USER_PRICE"]
    elif filename == "employees.py":
        needs_config_imports = ["SUBSCRIPTION_PLANS"]
    elif filename == "checkout.py":
        needs_config_imports = ["SUBSCRIPTION_PLANS"]
        needs_email_imports = ["send_payment_confirmation_email", "send_invoice_email"]
    elif filename == "auth.py":
        # auth.py already imports get_current_user from utils.auth
        needs_auth_import = False
        needs_config_imports = ["SUBSCRIPTION_PLANS"]
        needs_email_imports = ["send_welcome_email"]
    
    # --- Step 2: Remove global variable declarations ---
    
    # Remove db = None
    content = re.sub(r'^db\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove _get_current_user_func = None or similar
    content = re.sub(r'^_get_current_user_func[\s:]*.*=\s*None\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove SUBSCRIPTION_PLANS = None (for subscriptions, employees)
    if "SUBSCRIPTION_PLANS" in needs_config_imports:
        content = re.sub(r'^SUBSCRIPTION_PLANS\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^SUBSCRIPTION_PLANS\s*=\s*\{\}\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove FEATURE_ACCESS = None
    if "FEATURE_ACCESS" in needs_config_imports:
        content = re.sub(r'^FEATURE_ACCESS\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove ADDITIONAL_USER_PRICE = 2.5 declaration (it will be imported)
    if "ADDITIONAL_USER_PRICE" in needs_config_imports:
        content = re.sub(r'^ADDITIONAL_USER_PRICE\s*=\s*[\d.]+\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove email function globals for checkout.py
    if filename == "checkout.py":
        content = re.sub(r'^_send_payment_confirmation_email\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'^_send_invoice_email\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
    
    # Remove send_welcome_email = None for auth.py
    if filename == "auth.py":
        content = re.sub(r'^send_welcome_email\s*=\s*None\s*\n', '', content, flags=re.MULTILINE)
    
    # --- Step 3: Remove init_router function ---
    # Match the function definition and its body (indented lines)
    content = re.sub(
        r'^def init_router\(.*?\):\s*\n(?:[ \t]+.*\n)*',
        '',
        content,
        flags=re.MULTILINE
    )
    
    # --- Step 4: Remove local get_current_user wrapper ---
    if has_local_auth and filename != "auth.py":
        # Remove the async def get_current_user wrapper function
        # Match: async def get_current_user(...): followed by indented body
        content = re.sub(
            r'^async def get_current_user\(.*?\):\s*\n(?:[ \t]+.*\n)*',
            '',
            content,
            flags=re.MULTILINE
        )
    
    # --- Step 5: Add imports ---
    
    # Find the right place to add imports (after the existing imports block)
    # Strategy: Add after the router = APIRouter(...) line
    
    import_lines = []
    
    if needs_db_import:
        # Check if already imported
        if not re.search(r'from config import.*\bdb\b', content):
            import_lines.append("from config import db")
    
    if needs_auth_import:
        if not re.search(r'from utils\.auth import.*get_current_user', content):
            import_lines.append("from utils.auth import get_current_user")
    
    if needs_config_imports:
        # Check what's already imported from config
        existing_config = re.search(r'from config import (.+)', content)
        existing_items = set()
        if existing_config:
            existing_items = {x.strip() for x in existing_config.group(1).split(',')}
        
        new_items = [item for item in needs_config_imports if item not in existing_items]
        
        if new_items:
            if existing_config:
                # Add to existing config import
                all_items = list(existing_items) + new_items
                new_import = f"from config import {', '.join(sorted(all_items))}"
                content = re.sub(r'from config import .+', new_import, content, count=1)
            else:
                import_lines.append(f"from config import {', '.join(new_items)}")
    
    if needs_email_imports:
        if not re.search(r'from email_service import', content):
            import_lines.append(f"from email_service import {', '.join(needs_email_imports)}")
        else:
            # Check what's already imported
            existing_email = re.search(r'from email_service import (.+)', content)
            if existing_email:
                existing_items = {x.strip() for x in existing_email.group(1).split(',')}
                new_items = [item for item in needs_email_imports if item not in existing_items]
                if new_items:
                    all_items = list(existing_items) + new_items
                    new_import = f"from email_service import {', '.join(all_items)}"
                    content = re.sub(r'from email_service import .+', new_import, content, count=1)
    
    # Insert new imports after the router declaration
    if import_lines:
        import_block = '\n'.join(import_lines)
        # Insert after router = APIRouter(...)
        router_match = re.search(r'^router\s*=\s*APIRouter\(.*?\)\s*\n', content, re.MULTILINE)
        if router_match:
            insert_pos = router_match.end()
            content = content[:insert_pos] + import_block + '\n' + content[insert_pos:]
        else:
            # Fallback: insert at the top after existing imports
            content = import_block + '\n' + content
    
    # --- Step 6: Fix checkout.py specific references ---
    if filename == "checkout.py":
        # Replace _send_payment_confirmation_email with send_payment_confirmation_email
        content = content.replace('_send_payment_confirmation_email', 'send_payment_confirmation_email')
        content = content.replace('_send_invoice_email', 'send_invoice_email')
    
    # --- Step 7: Clean up extra blank lines (3+ consecutive -> 2) ---
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # --- Step 8: Remove "# Will be initialized by init_router" comments ---
    content = re.sub(r'^#\s*(?:Will be|These will be|MongoDB reference).*init_router.*\n', '', content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'^#\s*These will be injected.*\n', '', content, flags=re.MULTILINE)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False


# Run refactoring
changed = []
errors = []

for filename in sorted(os.listdir(ROUTES_DIR)):
    if not filename.endswith('.py'):
        continue
    filepath = os.path.join(ROUTES_DIR, filename)
    try:
        if refactor_file(filepath):
            changed.append(filename)
            print(f"  REFACTORED: {filename}")
        else:
            print(f"  SKIPPED: {filename}")
    except Exception as e:
        errors.append((filename, str(e)))
        print(f"  ERROR: {filename} - {e}")

print(f"\n{'='*50}")
print(f"Refactored: {len(changed)} files")
print(f"Errors: {len(errors)}")
if errors:
    for f, e in errors:
        print(f"  {f}: {e}")
