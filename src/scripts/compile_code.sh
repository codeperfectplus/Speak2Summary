#!/bin/bash

set -euo pipefail
trap 'echo "❌ Error occurred. Exiting..."; exit 1' ERR

# Constants
readonly ROOT_DIRECTORY=$(pwd)
readonly COMPILED_CODE_SOURCE_DIRECTORY="$ROOT_DIRECTORY/build"

# Comma-separated list of excluded Python files (relative to root, e.g., "main.py" or "tools/start.py")
EXCLUDE_FILES=()

log() {
    echo -e "\033[1;34m[INFO]\033[0m $*"
}

safe_copy() {
    cp -r "$1" "$2" || { echo "Error: Failed to copy $1"; exit 1; }
}

icd_excluded() {
    local rel_path="$1"
    for excluded in "${EXCLUDE_FILES[@]}"; do
        [[ "$rel_path" == "$excluded" ]] && return 0
    done
    return 1
}

prepare_output_dirs() {
    log "Preparing output directories..."
    mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY"
    find . -type d ! -path "./compiled_code*" \
                  ! -path "*/.git*" \
                  ! -path "*/__pycache__*" | while read -r dir; do
        mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY/${dir#./}"
    done
}


compile_python_files() {
    log "Converting Python files to shared objects..."
    find . -name '*.py' ! -path "./compiled_code/*" \
                        ! -path "*/.git/*" \
                        ! -path "*/__pycache__/*" | while read -r py_file; do
        rel_path="${py_file#./}"
        if is_excluded "$rel_path"; then
            log "Excluded: $rel_path"
            cp "$py_file" "$COMPILED_CODE_SOURCE_DIRECTORY/$rel_path"
            continue
        fi

        if ! grep -q "# cython: language_level=" "$py_file"; then
            echo "# cython: language_level=3" | cat - "$py_file" > tmp && mv tmp "$py_file"
        fi

        c_file="${py_file%.py}.c"
        cython "$py_file" -o "$c_file"

        output_dir="$(dirname "$COMPILED_CODE_SOURCE_DIRECTORY/$rel_path")"
        base_name="$(basename "$py_file" .py)"
        gcc -shared -o "$output_dir/$base_name.so" -fPIC $(python3 -m pybind11 --includes) "$c_file"

        rm "$c_file"
    done
}

is_excluded() {
    local rel_path="$1"
    for excluded in "${EXCLUDE_FILES[@]}"; do
        [[ "$rel_path" == "$excluded" ]] && return 0
    done
    return 1
}


copy_other_files() {
    log "Copying non-Python files..."
    find . -type f ! -name '*.py' ! -name '*.c' \
        ! -path "./compiled_code/*" \
        ! -path "*/.git/*" \
        ! -path "*/__pycache__/*" | while read -r file; do
        rel_path="${file#./}"
        target_path="$COMPILED_CODE_SOURCE_DIRECTORY/$rel_path"
        mkdir -p "$(dirname "$target_path")"
        cp "$file" "$target_path"
    done
}


# Optional cleanup (build artifacts)
cleanup() {
    log "Cleaning up temporary files..."
    rm -rf build
}

# Time tracking
start_timer() { date +%s.%N; }
elapsed_time() { echo "$(echo "$(date +%s.%N) - $1" | bc)"; }

# ------------------ EXECUTION ------------------

log "🚀 Build started from current directory..."
mkdir -p "$COMPILED_CODE_SOURCE_DIRECTORY"
start=$(start_timer)
prepare_output_dirs
compile_python_files
copy_other_files
log "✅ Build completed in $(elapsed_time "$start") seconds"

log "🎉 Compiled project is in: $COMPILED_CODE_SOURCE_DIRECTORY"
