import os
import subprocess
import json
import logging
import anyio

logger = logging.getLogger(__name__)

async def run_uipath_automation(process_name_or_path: str, arguments: dict = None, is_file: bool = False):
    """
    Runs a UiPath automation using UiRobot.exe asynchronously.
    """
    def _run_sync():
        nonlocal process_name_or_path
        ui_robot_path = os.getenv("UI_ROBOT_PATH")
        
        if not ui_robot_path:
            error_msg = "UI_ROBOT_PATH not found in environment variables."
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        if not os.path.exists(ui_robot_path):
            error_msg = f"UiRobot.exe not found at path: {ui_robot_path}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Construct the command
        command = [ui_robot_path, "execute"]
        
        if is_file:
            publish_folder = os.getenv("PUBLISH_AUTOMATION_FOLDER")
            logger.info(f"Using PUBLISH_AUTOMATION_FOLDER: {publish_folder}")
            if publish_folder and not os.path.isabs(process_name_or_path):
                process_name_or_path = os.path.join(publish_folder, process_name_or_path)
            command.extend(["--file", process_name_or_path])
        else:
            command.extend(["--process", process_name_or_path])
            
        if arguments:
            command.extend(["--input", json.dumps(arguments)])

        try:
            logger.info(f"Executing UiPath command: {' '.join(command)}")
            # This is the blocking call we run in a thread
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            logger.info(f"Subprocess finished with return code: {result.returncode}")
            
            if result.returncode == 0:
                logger.info("UiPath automation executed successfully.")
                return {
                    "status": "success", 
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                logger.error(f"UiPath automation failed with exit code {result.returncode}: {result.stderr}")
                return {
                    "status": "error", 
                    "message": result.stderr,
                    "exit_code": result.returncode
                }
        except Exception as e:
            logger.error(f"Exception while running UiPath automation: {e}")
            return {"status": "error", "message": str(e)}

    # Run the sync function in a separate thread to keep the event loop free
    return await anyio.to_thread.run_sync(_run_sync)
