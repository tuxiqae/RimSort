#!/usr/bin/env bash

set -e # Exit on error
set -u # Error if an unassigned variable is called

# Detect the operating system
os=$(uname)
APP_BASE_NAME=RimSort
declare -rA SUPPORTED_OSES=(["Darwin"]="macOS" ["Linux"]="Linux")

pretty_print_aarray_values() {
    local IFS=", "
    echo "$*"
}

if [[ -z "${SUPPORTED_OSES["$os"]}" ]]; then
    echo "The operating system in use ${os} is unsupported, please use once of the following ($(pretty_print_aarray_values "${SUPPORTED_OSES[@]}"))"
    exit 1
fi

# Set the update source folder based on the OS
if [[ "$os" = "Darwin" ]]; then
    # macOS detected
    executable_name="${APP_BASE_NAME}.app"
    grandparent_dir="$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")"
    update_source_folder="${TMPDIR:-/tmp}"
elif [[ "$os" = "Linux" ]]; then
    executable_name="${APP_BASE_NAME}.bin"
    parent_dir=$(readlink -f -- "$(dirname -- "$0")")
    update_source_folder="/tmp/RimSort"
fi

# Ensure the application is killed
killall -q -- "$executable_name" || true

# Display a message indicating the update operation is starting in 5 seconds
read -r -t 5 -p "Updating RimSort in 5 seconds. Press Enter to continue."

# Execute RimSort from the current directory
if [[ "$os" = "Darwin" ]]; then # macOS detected
    # Remove old installation
    rm -rf -- "${grandparent_dir}"
    # Move files from the update source folder to the current directory
    chmod +x -- "${update_source_folder}/${executable_name}/Contents/MacOS/RimSort" "${update_source_folder}/${executable_name}/Contents/MacOS/todds/todds"
    mv -- "${update_source_folder}/${executable_name}" "${grandparent_dir}"
    open -- "${grandparent_dir}"
elif [[ "$os" = "Linux" ]]; then
    # Remove old installation
    rm -rf -- "${parent_dir}"
    # Move files from the update source folder to the current directory
    chmod +x -- "${update_source_folder}/${executable_name}" "${update_source_folder}/todds/todds"
    mv "${update_source_folder}" "${parent_dir}"
    "${parent_dir}/$executable_name"
fi
