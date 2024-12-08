import os
import subprocess

# Directory where YAML files were generated
output_dir = "generated_yamls"

# Check if the directory exists
if os.path.exists(output_dir):
    # Iterate through all files in the directory
    for yaml_file in os.listdir(output_dir):
        yaml_path = os.path.join(output_dir, yaml_file)

        # Ensure the file is a YAML file
        if yaml_file.endswith(".yaml"):
            # Run kubectl delete -f for the YAML file
            try:
                subprocess.run(["kubectl", "delete", "-f", yaml_path], check=False)
                print(f"Successfully deleted resources defined in {yaml_file}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to delete resources defined in {yaml_file}. Error: {e}")

    # Once all YAML files are processed, delete the directory
    try:
        # Remove all files in the directory
        for yaml_file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, yaml_file))
        # Remove the directory itself
        os.rmdir(output_dir)
        print(f"Cleaned up directory: {output_dir}")
    except Exception as e:
        print(f"Error while cleaning up directory {output_dir}. Error: {e}")
else:
    print(f"Directory {output_dir} does not exist.")
