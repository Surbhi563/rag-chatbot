#!/bin/bash

# APAC Atlas Taxonomy Service - Development Script
# This script runs the complete development workflow: install, test, and start

set -e  # Exit on any error

echo "🛠️  Starting development workflow for APAC Atlas Taxonomy Service..."
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
./scripts/install.sh
echo ""

# Step 2: Start server
echo "🚀 Step 2: Starting development server..."
echo "   (This will run in the foreground. Press Ctrl+C to stop)"
echo ""
./scripts/start.sh
