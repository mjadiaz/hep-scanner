#!/bin/bash

echo "The first argument is: $1"
echo "The second argument is: $2"
echo "The third argument is: $3"
if [ -z "$1" ]; then
  echo "Error: Please provide a filename as the first argument."
  exit 1
fi