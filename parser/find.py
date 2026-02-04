'''
Find and copy dictionaries into specified folder

'''
import os
import shutil

import os
import shutil

def copy_files_with_specific_lang(src_dir, dst_dir, skip_language, add_language):
    # Create destination folder if it doesn't exist
    os.makedirs(dst_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            filename_lower = file.lower()

            # Skip if the file has any of the unwanted patterns
            if any(x in filename_lower for x in skip_language):
                continue

            # Copy only if 'en' or 'eng' is present
            if add_language in filename_lower:
                src_path = os.path.join(root, file)
                dst_path = os.path.join(dst_dir, file)
                print(f"Copying {src_path} to {dst_path}")
                shutil.copy2(src_path, dst_path) # use copy2 or move

if __name__ == "__main__":
    source_folder = "/dir/"
    destination_folder = "/dir/"
    
    copy_files_with_specific_lang(source_folder, destination_folder)