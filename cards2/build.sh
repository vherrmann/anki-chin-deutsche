mkdir -p build

for f in $(find ./card* -type f); do
    echo "$f"
    mkdir -p $(dirname "./build/$f")
    cat "./common/$(basename $f)" "$f" > "./build/$f"
done
