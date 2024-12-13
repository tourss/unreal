import os

# Define the desired path for the 'render_logs' folder
log_dir = r"C:\Users\admin\Desktop\Project\pipe_test\Saved\Logs\render_logs"

# Check if the folder exists, if not, create it
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    print(f"Folder created at: {log_dir}")
else:
    print(f"Folder already exists at: {log_dir}")
