#!/bin/bash
# Remind Installation Script
# Install via: curl -sSL https://remind.hamzaplojovic.blog/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS and architecture
detect_platform() {
    OS=$(uname -s)
    ARCH=$(uname -m)

    case "$OS" in
        Darwin)
            PLATFORM="macos"
            if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
                BINARY_ARCH="arm64"
            else
                BINARY_ARCH="x86_64"
            fi
            ;;
        Linux)
            PLATFORM="linux"
            case "$ARCH" in
                x86_64)
                    BINARY_ARCH="x86_64"
                    ;;
                aarch64|arm64)
                    echo -e "${YELLOW}⚠ Linux ARM64 not yet supported${NC}"
                    echo -e "${YELLOW}Please use macOS or x86_64 Linux for now${NC}"
                    exit 1
                    ;;
                *)
                    echo -e "${RED}✗ Unsupported architecture: $ARCH${NC}"
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo -e "${RED}✗ Unsupported OS: $OS${NC}"
            exit 1
            ;;
    esac

    echo -e "${BLUE}Detected: $PLATFORM ($BINARY_ARCH)${NC}"
}

# Install on macOS via Homebrew
install_macos() {
    echo -e "\n${BLUE}Installing Remind for macOS...${NC}"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Install via Homebrew tap
    brew tap hamzaplojovic/remind https://github.com/hamzaplojovic/homebrew-remind
    brew install remind-cli

    echo -e "${GREEN}✓ Remind installed successfully${NC}"
    echo -e "\nQuick start:"
    echo -e "  ${BLUE}remind add${NC} 'Buy groceries' --due 'tomorrow 5pm'"
    echo -e "  ${BLUE}remind list${NC}"
    echo -e "  ${BLUE}remind done${NC} 1"
}

# Install on Linux via direct binary download
install_linux() {
    echo -e "\n${BLUE}Installing Remind for Linux...${NC}"

    # Check for curl and other dependencies
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}✗ curl is required${NC}"
        exit 1
    fi

    # Get the latest release version
    echo -e "${BLUE}Fetching latest release...${NC}"
    LATEST_RELEASE=$(curl -s https://api.github.com/repos/hamzaplojovic/remind/releases/latest | grep '"tag_name"' | cut -d'"' -f4)

    if [ -z "$LATEST_RELEASE" ]; then
        echo -e "${RED}✗ Could not determine latest release${NC}"
        exit 1
    fi

    BINARY_URL="https://github.com/hamzaplojovic/remind/releases/download/${LATEST_RELEASE}/remind-linux-${BINARY_ARCH}"
    CHECKSUM_URL="https://github.com/hamzaplojovic/remind/releases/download/${LATEST_RELEASE}/SHA256SUMS"

    # Download binary
    echo -e "${BLUE}Downloading remind binary (${LATEST_RELEASE})...${NC}"
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    if ! curl -fsSL -o "$TEMP_DIR/remind" "$BINARY_URL"; then
        echo -e "${RED}✗ Failed to download remind binary${NC}"
        echo -e "${YELLOW}Try installing via Homebrew instead:${NC}"
        echo -e "  brew tap hamzaplojovic/remind"
        echo -e "  brew install remind-cli"
        exit 1
    fi

    # Verify checksum
    echo -e "${BLUE}Verifying checksum...${NC}"
    if curl -fsSL -o "$TEMP_DIR/SHA256SUMS" "$CHECKSUM_URL"; then
        cd "$TEMP_DIR"
        if ! sha256sum -c SHA256SUMS 2>/dev/null | grep -q "remind-linux-${BINARY_ARCH}.*OK"; then
            echo -e "${RED}✗ Checksum verification failed${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Checksum verified${NC}"
        cd - > /dev/null
    else
        echo -e "${YELLOW}⚠ Could not verify checksum (continuing anyway)${NC}"
    fi

    # Install binary
    chmod +x "$TEMP_DIR/remind"
    echo -e "${BLUE}Installing to /usr/local/bin/remind...${NC}"

    if ! sudo mv "$TEMP_DIR/remind" /usr/local/bin/remind; then
        echo -e "${RED}✗ Installation failed (permission denied)${NC}"
        echo -e "${YELLOW}Try running with sudo:${NC}"
        echo -e "  sudo bash"
        exit 1
    fi

    echo -e "${GREEN}✓ Remind installed successfully${NC}"
    echo -e "\nQuick start:"
    echo -e "  ${BLUE}remind add${NC} 'Buy groceries' --due 'tomorrow 5pm'"
    echo -e "  ${BLUE}remind list${NC}"
    echo -e "  ${BLUE}remind done${NC} 1"
}

# Verify installation
verify_installation() {
    echo -e "\n${BLUE}Verifying installation...${NC}"

    if command -v remind &> /dev/null; then
        VERSION=$(remind --version 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓ remind installed: $VERSION${NC}"
    else
        echo -e "${RED}✗ Installation verification failed${NC}"
        exit 1
    fi
}

# Setup daemon (automatic)
setup_daemon() {
    echo -e "${BLUE}Setting up background scheduler...${NC}"

    if remind scheduler --enable > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Background scheduler enabled${NC}"

        # Send daemon setup notification
        if [ "$PLATFORM" = "macos" ]; then
            osascript -e 'display notification "Background scheduler is running and will check for reminders every 5 minutes" with title "Remind Daemon Started"' 2>/dev/null || true
        elif [ "$PLATFORM" = "linux" ]; then
            notify-send --app-name "Remind" "Daemon Started" "Background scheduler is running and will check for reminders every 5 minutes" 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}⚠ Could not enable background scheduler${NC}"
        echo -e "You can enable it manually later with: ${BLUE}remind scheduler --enable${NC}"
    fi
}

# Show success notification
show_success_notification() {
    echo
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Remind CLI installed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo

    # Send comprehensive installation success notification
    if [ "$PLATFORM" = "macos" ]; then
        osascript -e 'display notification "Installation complete! Daemon is running and ready to send reminders." with title "Remind Installation Complete"' 2>/dev/null || true
    elif [ "$PLATFORM" = "linux" ]; then
        notify-send --app-name "Remind" "Installation Complete" "Daemon is running and ready to send reminders" 2>/dev/null || true
    fi

    echo -e "Quick start:"
    echo -e "  ${BLUE}remind add${NC} 'Buy groceries' --due 'tomorrow 5pm'"
    echo -e "  ${BLUE}remind list${NC} - view all reminders"
    echo -e "  ${BLUE}remind done${NC} 1 - mark reminder as done"
    echo
    echo -e "Background scheduler: ${GREEN}enabled${NC}"
    echo -e "Check reminders every: ${GREEN}5 minutes${NC}"
    echo -e "Notifications: ${GREEN}enabled${NC}"
    echo
    echo -e "Helpful commands:"
    echo -e "  ${BLUE}remind scheduler --status${NC} - check scheduler status"
    echo -e "  ${BLUE}remind scheduler --disable${NC} - turn off background reminders"
    echo -e "  ${BLUE}remind help${NC} - see all available commands"
    echo
}

# Main installation flow
main() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════╗"
    echo "║  Remind: AI-Powered Reminder CLI       ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"

    detect_platform

    if [ "$PLATFORM" = "macos" ]; then
        install_macos
    elif [ "$PLATFORM" = "linux" ]; then
        install_linux
    fi

    verify_installation
    setup_daemon
    show_success_notification
}

main
