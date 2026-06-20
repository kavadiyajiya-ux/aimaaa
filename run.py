import subprocess
import sys
import time

def main():
    print("Starting AIMA Unified Platform...")
    print("=====================================")
    
    # 1. Start FastAPI Backend (Employee Portal)
    print("-> Launching FastAPI Backend & HTML Portal on port 8000...")
    fastapi_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
    )
    
    # Give the backend a second to bind the port
    time.sleep(2)
    
    # 2. Start Streamlit (Admin Dashboard)
    print("-> Launching Streamlit Admin Dashboard on port 8501...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py"]
    )
    
    print("\nAll systems are online!")
    print("- Employee Portal: http://localhost:8000")
    print("- Admin Dashboard: http://localhost:8501\n")
    print("Press Ctrl+C to gracefully shut down all servers.")
    
    try:
        # Keep the main thread alive, waiting for both processes
        fastapi_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down AIMA systems...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        fastapi_process.wait()
        streamlit_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
