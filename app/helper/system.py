import winreg

def get_machine_guid() -> str:
    """
    Retrieves the machine GUID from the Windows Registry.
    Location: HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return guid
    except Exception as e:
        # Fallback or re-raise depending on requirements. 
        # For a server that must identify itself uniquely, failing here is significant.
        print(f"Error retrieving MachineGuid: {e}")
        return "unknown-guid"
