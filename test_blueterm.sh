#!/bin/bash
# Quick test script for blueterm
echo "Testing blueterm with API key..."
export IBMCLOUD_API_KEY=$(scrt get ntl-mkt-account-apikey)
if [ -z "$IBMCLOUD_API_KEY" ]; then
    echo "Error: Could not retrieve API key from scrt"
    exit 1
fi
echo "API key loaded successfully"
python -m blueterm
