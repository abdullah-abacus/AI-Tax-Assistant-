"""
Main Entry Point for KRA Tax Assistant
Initializes database and provides CLI menu
"""
import os
import sys
from src.database.db_manager import initialize_database

def print_banner():
    print("\n" + "="*80)
    print("🇰🇪  KRA AI TAX ASSISTANT")
    print("="*80)
    print("Powered by Google ADK + Gemini 2.5 Pro + Chainlit")
    print("="*80 + "\n")

def show_menu():
    print("\nSelect an option:")
    print("1. Start Chainlit App (Taxpayer Interface)")
    print("2. Start Admin Dashboard (Officer Interface - Web)")
    print("3. View Officer Dashboard (CLI - Audit Cases)")
    print("4. Initialize/Reset Database")
    print("5. Exit")
    return input("\nYour choice: ")

def run_chainlit():
    print("\n🚀 Starting Chainlit app (Taxpayer Interface)...")
    print("Visit: http://localhost:8000")
    # Use the current Python executable to run Chainlit as a module.
    # This avoids relying on the "chainlit" CLI being on the OS PATH,
    # and just requires the package to be installed in this virtualenv.
    os.system(f'"{sys.executable}" -m chainlit run src/ui/chainlit_app.py')

def run_admin_dashboard():
    print("\n🚀 Starting Admin Dashboard (Officer Interface)...")
    print("Visit: http://localhost:8001")
    print("Note: This is a separate instance from the taxpayer interface.")
    os.system(f'"{sys.executable}" -m chainlit run src/ui/admin_dashboard.py --port 8001')

def run_dashboard():
    from src.ui.officer_dashboard import display_dashboard, view_case_details
    display_dashboard()
    
    while True:
        action = input("\nEnter KRA PIN to view details (or 'back' to return): ")
        if action.lower() == 'back':
            break
        view_case_details(action)

def init_db():
    print("\n📦 Initializing database...")
    try:
        initialize_database()
        print("✅ Database initialized successfully!")
        print("   - Schema created")
        print("   - Mock data seeded")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print_banner()
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  WARNING: .env file not found!")
        print("Please copy .env.example to .env and add your Google API key.")
        print("Get your key from: https://ai.google.dev/")
        print("\nContinuing anyway...\n")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_chainlit()
        elif choice == '2':
            run_admin_dashboard()
        elif choice == '3':
            run_dashboard()
        elif choice == '4':
            init_db()
        elif choice == '5':
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main()
