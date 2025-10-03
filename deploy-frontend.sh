#!/bin/bash

# Frontend deployment script
echo "Building frontend..."

cd frontend

# Install dependencies
npm install

# Build the React app
npm run build

echo "Frontend built successfully!"
echo "To deploy:"
echo "1. Go to https://vercel.com"
echo "2. Import your GitHub repository"
echo "3. Set root directory to 'frontend'"
echo "4. Deploy!"
echo ""
echo "Or run locally:"
echo "npm start"
