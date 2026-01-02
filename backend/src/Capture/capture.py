import subprocess
import logging
import os
import shutil
import config

def capture_packets_tshark(capture_duration):
    """
    Capture network packets using tshark for the specified duration.
    
    Args:
        capture_duration (int): Duration in seconds to capture packets
        
    Raises:
        FileNotFoundError: If tshark is not installed or not found
        subprocess.CalledProcessError: If capture command fails
        Exception: For other capture-related errors
    """
    # Check if tshark is available
    tshark_paths = [
        "C:\\Program Files\\Wireshark\\tshark.exe",
        "C:\\Program Files (x86)\\Wireshark\\tshark.exe",
        "tshark"  # If in PATH
    ]
    
    tshark_path = None
    for path in tshark_paths:
        if path == "tshark":
            # Check if tshark is in PATH
            if shutil.which("tshark"):
                tshark_path = "tshark"
                break
        elif os.path.exists(path):
            tshark_path = f'"{path}"'
            break
    
    if not tshark_path:
        raise FileNotFoundError("Wireshark/tshark is not installed or not found in expected locations. Please install Wireshark to use packet capture functionality.")
    
    try:
        # Use config path for saving capture file
        output_path = config.PCAP_SAVE_PATH
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try different network interfaces
        interfaces = ["Wi-Fi", "Ethernet", "any"]
        
        for interface in interfaces:
            try:
                command = f'{tshark_path} -i {interface} -a duration:{capture_duration} -w "{output_path}"'
                logging.info(f"Attempting to capture on interface: {interface}")
                subprocess.run(command, shell=True, check=True, timeout=capture_duration + 10)
                logging.info(f"Packet capture completed successfully on interface: {interface}")
                return
            except subprocess.CalledProcessError as e:
                logging.warning(f"Failed to capture on interface {interface}: {e}")
                continue
        
        # If all interfaces failed
        raise Exception("Failed to capture packets on any available network interface")
        
    except subprocess.TimeoutExpired:
        logging.error("Packet capture timed out")
        raise Exception("Packet capture operation timed out")
    except subprocess.CalledProcessError as e:
        logging.error(f"Capture command failed: {e}")
        raise Exception(f"Packet capture failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected capture error: {e}")
        raise

def capture_packets_tshark_wrapper(capture_duration):
    """
    Wrapper function for packet capture with enhanced error handling.
    
    Args:
        capture_duration (int): Duration in seconds to capture packets
        
    Raises:
        Exception: Re-raises any exceptions from the capture process
    """
    try:
        capture_packets_tshark(capture_duration)
    except FileNotFoundError as e:
        logging.error(f"Dependency error: {str(e)}")
        raise Exception(f"Required software not found: {str(e)}")
    except Exception as e:
        logging.error(f"Capture error: {str(e)}")
        raise Exception(f"Packet capture failed: {str(e)}")