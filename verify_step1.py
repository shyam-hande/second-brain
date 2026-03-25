import os
import sys

print("=" * 50)
print("STEP 1 VERIFICATION")
print("=" * 50)

# Check folder structure
folders = [
    "src/agents", "src/memory", "src/rag", 
    "src/guardrails", "src/evaluation", "src/observability",
    "data/notes", "data/recipes", "data/transcriptions"
]

print("\n📁 Folder Structure:")
for folder in folders:
    exists = os.path.isdir(folder)
    print(f"  {'✅' if exists else '❌'} {folder}")

# Check key files
files = [".env", "src/config.py", "requirements.txt"]
print("\n📄 Key Files:")
for f in files:
    exists = os.path.isfile(f)
    print(f"  {'✅' if exists else '❌'} {f}")

# Check imports
print("\n📦 Package Imports:")
packages = {
    "pydantic_ai": "pydantic-ai",
    "chromadb": "chromadb",
    "anthropic": "anthropic",
    "rich": "rich",
    "tinydb": "tinydb",
    "dotenv": "python-dotenv",
}

all_good = True
for module, name in packages.items():
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ❌ {name} - run: pip install {name}")
        all_good = False

# Check config
print("\n⚙️  Config:")
try:
    from src.config import settings
    has_key = bool(settings.anthropic_api_key)
    print(f"  {'✅' if has_key else '❌'} ANTHROPIC_API_KEY {'is set' if has_key else 'is MISSING'}")
    print(f"  ✅ Model: {settings.model_name}")
except Exception as e:
    print(f"  ❌ Config error: {e}")
    all_good = False

# Check sample data
print("\n📝 Sample Data:")
data_files = [
    "data/notes/python_tips.md",
    "data/recipes/pasta_carbonara.md"
]
for f in data_files:
    exists = os.path.isfile(f)
    print(f"  {'✅' if exists else '❌'} {f}")

print("\n" + "=" * 50)
print("✅ Step 1 Complete! Ready for Step 2" if all_good else "❌ Fix errors above before Step 2")
print("=" * 50)