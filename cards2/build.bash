#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$SCRIPT_DIR"

mkdir -p build

for f in $(find ./card* -type f); do
    echo "$f"
    mkdir -p $(dirname "./build/$f")
    cat ./common/config.html ./common/libs/* ./common/common.html "./common/$(basename $f)" "$f" > "./build/$f"
done

popd
