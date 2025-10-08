#!/bin/bash
# Avatar Tank - Push to Existing GitHub Repository
# This script helps you push to your existing GitHub repository

echo "🚀 Avatar Tank - Push to Existing GitHub Repository"
echo "=================================================="
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

# Check if remote exists
if git remote get-url origin >/dev/null 2>&1; then
    print_info "Remote 'origin' configured:"
    git remote get-url origin
else
    print_info "Adding remote 'origin'..."
    git remote add origin https://github.com/rappzoo/Virtual-presence-Avatar.git
    print_success "Remote added: https://github.com/rappzoo/Virtual-presence-Avatar.git"
fi

echo ""
print_info "Authentication options:"
echo "1. Personal Access Token (Recommended)"
echo "2. SSH Key"
echo "3. GitHub CLI"
echo ""

read -p "Choose authentication method (1-3): " auth_method

case $auth_method in
    1)
        echo ""
        print_info "Using Personal Access Token method:"
        echo "1. Go to: https://github.com/settings/tokens"
        echo "2. Click 'Generate new token (classic)'"
        echo "3. Give it a name like 'Avatar Tank Upload'"
        echo "4. Select 'repo' scope"
        echo "5. Copy the token"
        echo ""
        read -p "Enter your Personal Access Token: " -s token
        echo ""
        
        if [[ -n "$token" ]]; then
            print_info "Pushing with Personal Access Token..."
            if git push https://$token@github.com/rappzoo/Virtual-presence-Avatar.git main; then
                print_success "🎉 Successfully pushed to GitHub!"
            else
                print_error "Failed to push. Check your token and try again."
            fi
        else
            print_error "No token provided."
        fi
        ;;
    2)
        echo ""
        print_info "Using SSH method:"
        git remote set-url origin git@github.com:rappzoo/Virtual-presence-Avatar.git
        print_info "Pushing with SSH..."
        if git push -u origin main; then
            print_success "🎉 Successfully pushed to GitHub!"
        else
            print_error "Failed to push. Make sure you have SSH keys set up."
            print_info "To set up SSH keys:"
            echo "1. Generate SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'"
            echo "2. Add to SSH agent: ssh-add ~/.ssh/id_ed25519"
            echo "3. Add public key to GitHub: cat ~/.ssh/id_ed25519.pub"
        fi
        ;;
    3)
        echo ""
        print_info "Using GitHub CLI method:"
        if command -v gh >/dev/null 2>&1; then
            print_info "GitHub CLI found. Authenticating..."
            gh auth login
            print_info "Pushing with GitHub CLI..."
            if git push -u origin main; then
                print_success "🎉 Successfully pushed to GitHub!"
            else
                print_error "Failed to push."
            fi
        else
            print_error "GitHub CLI not installed."
            print_info "Install with: sudo apt install gh"
        fi
        ;;
    *)
        print_error "Invalid option. Please choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
if git ls-remote --heads origin main >/dev/null 2>&1; then
    print_success "✅ Repository successfully updated on GitHub!"
    print_info "Visit: https://github.com/rappzoo/Virtual-presence-Avatar"
    echo ""
    print_info "Your Avatar Tank project is now live on GitHub with:"
    echo "• Complete source code (955 files)"
    echo "• Comprehensive documentation"
    echo "• Setup scripts and utilities"
    echo "• TTS engine with multiple languages"
    echo "• Professional project structure"
    echo ""
    print_success "🎉 Congratulations! Your project is ready for the community!"
else
    print_warning "⚠️  Push may have failed. Check the output above for errors."
fi
