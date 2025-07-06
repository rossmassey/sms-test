#!/usr/bin/env python3
"""
Demo runner script that starts both the backend and frontend for easy demonstration.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    print("🚀 SMS Outreach System - Demo Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    # Check if jank_ui exists
    if not Path("jank_ui/package.json").exists():
        print("❌ Error: jank_ui directory not found. Run this script from the project root.")
        sys.exit(1)
    
    print("📋 Starting demo components...")
    print()
    
    try:
        # Start backend
        print("🔧 Starting backend server...")
        backend_process = subprocess.Popen(
            [sys.executable, "run_dev.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give backend time to start
        time.sleep(3)
        
        # Check if backend started successfully
        backend_poll = backend_process.poll()
        if backend_poll is not None:
            # Get the actual error output
            stdout, stderr = backend_process.communicate()
            print("❌ Backend failed to start.")
            print("Error output:")
            if stderr:
                print(f"STDERR: {stderr}")
            if stdout:
                print(f"STDOUT: {stdout}")
            print("Make sure you have all dependencies installed and .env configured.")
            return
        
        print("✅ Backend started successfully at http://localhost:8000")
        print()
        
        # Start frontend
        print("🎨 Starting frontend demo UI...")
        print("📌 Frontend will open at http://localhost:3000")
        print()
        print("=" * 50)
        print("🎯 DEMO READY!")
        print("=" * 50)
        print("1. Add some customers")
        print("2. Start AI conversations")
        print("3. Mock customer responses")
        print("4. Try manual interventions")
        print()
        print("Press Ctrl+C to stop both servers")
        print("=" * 50)
        
        # Change to jank_ui directory and start React
        os.chdir("jank_ui")
        frontend_process = subprocess.run(
            ["npm", "start"],
            check=False
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down demo...")
        backend_process.terminate()
        print("✅ Demo stopped successfully")
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        if 'backend_process' in locals():
            backend_process.terminate()

if __name__ == "__main__":
    main() 