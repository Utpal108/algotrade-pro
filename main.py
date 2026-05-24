import schedule
import time
import subprocess
import os
from datetime import datetime

# ════════════════════════════════════════════════════════════
# MAIN SCHEDULER
# Runs all analysis automatically every morning
# ════════════════════════════════════════════════════════════

def run_script(script_path):
    """Run a Python script and log output"""
    print(f"\n{'='*50}")
    print(f"Running: {script_path}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*50)
    result = subprocess.run(
        ["python", script_path],
        capture_output=False
    )
    if result.returncode == 0:
        print(f"✅ {script_path} completed successfully")
    else:
        print(f"❌ {script_path} failed")

def morning_run():
    """Run all analysis every morning"""
    print(f"\n🌅 MORNING RUN STARTED")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1 — Fetch latest data
    run_script("data/fetch_data.py")

    # Step 2 — Run factor model
    run_script("analysis/factors.py")

    # Step 3 — Run BERT sentiment
    run_script("analysis/bert_batch.py")

    # Step 4 — Run portfolio optimizer
    run_script("portfolio/optimizer.py")

    # Step 5 — Run risk analysis
    run_script("portfolio/risk.py")

    print(f"\n✅ MORNING RUN COMPLETE")
    print(f"Dashboard is ready at http://localhost:8501")

def run_dashboard():
    """Start the Streamlit dashboard"""
    subprocess.Popen(["streamlit", "run", "dashboard/app.py"])
    print("✅ Dashboard started at http://localhost:8501")

if __name__ == "__main__":
    print("=" * 50)
    print("ALGOTRADE PRO — SCHEDULER")
    print("=" * 50)
    print("\nOptions:")
    print("1. Run morning analysis now")
    print("2. Schedule daily at 9:00 AM")
    print("3. Start dashboard only")

    choice = input("\nEnter choice (1/2/3): ")

    if choice == "1":
        morning_run()

    elif choice == "2":
        print("\n⏰ Scheduling daily run at 9:00 AM...")
        schedule.every().day.at("09:00").do(morning_run)
        print("Scheduler running. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(60)

    elif choice == "3":
        run_dashboard()