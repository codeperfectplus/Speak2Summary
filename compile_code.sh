#!/bin/bash

set -euo pipefail
trap 'echo "❌ Error occurred. Exiting..."; exit 1' ERR

# Constants
readonly ROOT_DIRECTORY=$(pwd)
readonly SOURCE_DIRECTORY="$ROOT_DIRECTORY/src"
readonly COMPILED_CODE_DIRECTORY="$ROOT_DIRECTORY/compiled_code"
readonly COMPILED_CODE_SOURCE_DIRECTORY="$COMPILED_CODE_DIRECTORY/src"


log() {
    echo -e "\033[1;34m[INFO]\033[0m $*"
}

safe_copy() {
    cp -r "$1" "$2" || { echo "Error: Failed to copy $1"; exit 1; }
}

find_python_files() {
    find "$SOURCE_DIRECTORY" -name '*.py' -print0
}

find_c_files() {
    find "$SOURCE_DIRECTORY" -name '*.c' -print0
}

generate_c_files_parallel() {
    log "Generating C files from Python in parallel..."
    find_python_files | xargs -0 -n 1 -P "$(nproc)" -I {} bash -c '
        f="{}"
        if ! grep -q "# cython: language_level=" "$f"; then
            echo "# cython: language_level=3" | cat - "$f" > tmp && mv tmp "$f"
        fi
        cython "$f" -o "${f%.py}.c"
    '
}

compile_c_to_so_parallel() {
    log "Compiling .c files to .so in parallel..."
    find_c_files | xargs -0 -n 1 -P "$(nproc)" -I {} bash -c '
        c_file="{}"
        source_dir="'"$SOURCE_DIRECTORY"'"
        output_dir="'"$COMPILED_CODE_SOURCE_DIRECTORY"'"
        relative_path="${c_file#$source_dir/}"
        output_subdir="$(dirname "$relative_path")"
        mkdir -p "$output_dir/$output_subdir"
        base_name="$(basename "$c_file" .c)"
        gcc -shared -o "$output_dir/$output_subdir/$base_name.so" -fPIC $(python3 -m pybind11 --includes) "$c_file"
    '
}

copy_files() {
    log "Copying project files..."
    safe_copy requirements.txt "$COMPILED_CODE_DIRECTORY"
    safe_copy Dockerfile "$COMPILED_CODE_DIRECTORY"
    safe_copy docker-compose.yml "$COMPILED_CODE_DIRECTORY"
    safe_copy run.sh "$COMPILED_CODE_DIRECTORY"
}

cleanup() {
    log "Cleaning up generated C files..."
    find "$SOURCE_DIRECTORY" -name "*.c" -delete
    rm -rf build
}

# Time tracking
start_timer() {
    date +%s.%N
}

elapsed_time() {
    start=$1
    end=$(date +%s.%N)
    echo "$(echo "$end - $start" | bc)"
}

# ------------------ EXECUTION ------------------

log "🚀 Build started..."

start=$(start_timer)
copy_files
log "✅ Files copied in $(elapsed_time "$start") seconds"

start=$(start_timer)
generate_c_files_parallel
log "✅ C files generated in $(elapsed_time "$start") seconds"

start=$(start_timer)
compile_c_to_so_parallel
log "✅ Shared objects compiled in $(elapsed_time "$start") seconds"

# Optional cleanup
# cleanup

log "🎉 Build completed successfully."
