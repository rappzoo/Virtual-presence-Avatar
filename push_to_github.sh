#!/bin/bash
# Avatar Tank - Push to GitHub Script
# This script helps you push your Avatar Tank project to GitHub

echo "🚀 Avatar Tank - Push to GitHub"
echo "==============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository. Run 'git init' first."
    exit 1
fi

# Check if we have commits
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    print_error "No commits found. Make an initial commit first."
    exit 1
fi

print_info "Current repository status:"
git log --oneline -1
echo ""

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    print_info "Remote 'origin' already exists:"
    git remote get-url origin
    echo ""
    
    read -p "Do you want to use the existing remote? (y/n): " use_existing
    if [[ $use_existing != "y" && $use_existing != "Y" ]]; then
        print_info "Please provide the new GitHub repository URL:"
        read -p "GitHub repository URL: " repo_url
        
        if [[ -n "$repo_url" ]]; then
            git remote set-url origin "$repo_url"
            print_success "Remote URL updated to: $repo_url"
        else
            print_error "No URL provided. Exiting."
            exit 1
        fi
    fi
else
    print_info "No remote 'origin' found."
    print_info "Please provide your GitHub repository URL:"
    echo "Example: https://github.com/yourusername/avatar-tank.git"
    read -p "GitHub repository URL: " repo_url
    
    if [[ -n "$repo_url" ]]; then
        git remote add origin "$repo_url"
        print_success "Remote 'origin' added: $repo_url"
    else
        print_error "No URL provided. Exiting."
        exit 1
    fi
fi

echo ""
print_info "Pushing to GitHub..."

# Push to GitHub
if git push -u origin main; then
    print_success "🎉 Successfully pushed to GitHub!"
    echo ""
    print_info "Your Avatar Tank project is now available on GitHub!"
    print_info "Repository URL: $(git remote get-url origin)"
    echo ""
    print_info "Next steps:"
    echo "1. Visit your GitHub repository"
    echo "2. Add a repository description"
    echo "3. Enable GitHub Pages if desired"
    echo "4. Share with the community!"
    echo ""
    print_success "Happy coding! 🚀"
else
    print_error "Failed to push to GitHub."
    echo ""
    print_info "Common issues:"
    echo "1. Repository doesn't exist on GitHub - create it first"
    echo "2. Authentication issues - check your GitHub credentials"
    echo "3. Network issues - check your internet connection"
    echo ""
    print_info "To create a repository on GitHub:"
    echo "1. Go to https://github.com"
    echo "2. Click 'New repository'"
    echo "3. Name it 'avatar-tank' (or your preferred name)"
    echo "4. Don't initialize with README (we already have one)"
    echo "5. Click 'Create repository'"
    echo "6. Copy the repository URL and run this script again"
fi

