import sys
import os
import subprocess
import json
import time
import threading

def read_output(process, output_list):
    """Read output from the process stdout line by line."""
    for line in iter(process.stdout.readline, ''):
        if line:
            output_list.append(line)
    process.stdout.close()

def main():
    # Path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Command to run the server
    # We use python -m uniarticles to run it
    cmd = [sys.executable, "-m", "uniarticles"]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")

    # Start the server process
    process = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1 # Line buffered
    )

    # Thread to read stderr
    def print_stderr():
        for line in iter(process.stderr.readline, ''):
            print(f"SERVER LOG: {line.strip()}")
    
    stderr_thread = threading.Thread(target=print_stderr)
    stderr_thread.daemon = True
    stderr_thread.start()

    try:
        # Give it a moment to start
        time.sleep(2)
        
        # 1. Test: Initialize (MCP Protocol handshake)
        # Note: FastMCP handles initialization, but we can send list_tools directly 
        # as a quick check if it's running in stdio mode properly.
        # Standard MCP client sends "initialize" first.
        
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        
        print("\nSending 'initialize' request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        print(f"Received: {response_line.strip()}")
        
        if not response_line:
            print("Error: No response from server.")
            return

        response = json.loads(response_line)
        if "result" in response:
            print("✅ Initialize successful!")
        else:
            print(f"❌ Initialize failed: {response}")
            return

        # 2. Send initialized notification
        process.stdin.write(json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }) + "\n")
        process.stdin.flush()

        # 3. Test: List Tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\nSending 'tools/list' request...")
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        print(f"Received: {response_line.strip()[:200]}...") # Truncate for readability
        
        response = json.loads(response_line)
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            tool_names = [t["name"] for t in tools]
            print(f"✅ Tools found: {tool_names}")
            
            expected_tools = ["search_arxiv", "search_scopus", "search_semantic_scholar"]
            missing = [t for t in expected_tools if t not in tool_names]
            
            if not missing:
                print("✅ All expected tools are present.")
            else:
                print(f"⚠️ Missing tools: {missing}")
        else:
            print(f"❌ List tools failed: {response}")

    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        print("\nTerminating server...")
        process.terminate()
        process.wait()
        print("Done.")

if __name__ == "__main__":
    main()
