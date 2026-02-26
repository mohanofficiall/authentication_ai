import zipfile
import os

def zip_project(output_filename, source_dir):
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip unwanted directories
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', '.idea', '.vscode', 'node_modules', '.gemini']]
            
            for file in files:
                if file == output_filename or file.endswith('.zip') or file.endswith('.pyc'):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                try:
                    zipf.write(file_path, arcname)
                    print(f"Adding {arcname}")
                except Exception as e:
                    print(f"Skipping {arcname}: {e}")

if __name__ == "__main__":
    source_path = r'c:\Users\Suneel Reddy\Downloads\authentication'
    output_path = os.path.join(source_path, 'authentication_project.zip')
    
    print(f"Zipping {source_path} to {output_path}...")
    zip_project(output_path, source_path)
    print("Zip created successfully.")
