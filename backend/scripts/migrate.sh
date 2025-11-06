#!/bin/bash
# Database migration script for LDAP Web Manager
# Manages Alembic migrations to PostgreSQL

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | xargs)
else
    echo -e "${RED}Error: .env file not found at $PROJECT_ROOT/.env${NC}"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL not set in .env${NC}"
    exit 1
fi

# Function to display usage
usage() {
    cat << EOF
Database Migration Manager for LDAP Web Manager

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    current     Show current database revision
    history     Show migration history
    upgrade     Apply pending migrations (default: to head)
    downgrade   Revert migrations
    revision    Create new migration (requires message)
    merge       Merge migration branches
    heads       Show all migration heads
    branches    Show all branches

Options for 'upgrade' and 'downgrade':
    [revision]  Target revision (default: head for upgrade)

Examples:
    $0 current                          # Show current revision
    $0 upgrade                          # Upgrade to latest
    $0 upgrade 001_initial_schema       # Upgrade to specific revision
    $0 downgrade -1                     # Downgrade one revision
    $0 revision -m "Add new table"      # Create new migration

EOF
    exit 0
}

# Function to run alembic command
run_alembic() {
    cd "$BACKEND_DIR"
    python -m alembic "$@"
}

# Main script logic
if [ $# -eq 0 ]; then
    usage
fi

COMMAND="$1"
shift

case "$COMMAND" in
    current|--current|-c)
        echo -e "${GREEN}Current database revision:${NC}"
        run_alembic current
        ;;
    
    history|--history|-h)
        echo -e "${GREEN}Migration history:${NC}"
        run_alembic history
        ;;
    
    heads|--heads)
        echo -e "${GREEN}Migration heads:${NC}"
        run_alembic heads
        ;;
    
    branches|--branches)
        echo -e "${GREEN}Migration branches:${NC}"
        run_alembic branches
        ;;
    
    upgrade|--upgrade|-u)
        TARGET="${1:-head}"
        echo -e "${YELLOW}Upgrading database to: $TARGET${NC}"
        run_alembic upgrade "$TARGET"
        echo -e "${GREEN}Database upgraded successfully${NC}"
        ;;
    
    downgrade|--downgrade|-d)
        TARGET="$1"
        if [ -z "$TARGET" ]; then
            echo -e "${RED}Error: Target revision required for downgrade${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Downgrading database to: $TARGET${NC}"
        run_alembic downgrade "$TARGET"
        echo -e "${GREEN}Database downgraded successfully${NC}"
        ;;
    
    revision|--revision|-r)
        if [ $# -lt 2 ] || [ "$1" != "-m" ]; then
            echo -e "${RED}Error: Message required. Usage: $0 revision -m \"message\"${NC}"
            exit 1
        fi
        MESSAGE="$2"
        echo -e "${YELLOW}Creating migration: $MESSAGE${NC}"
        run_alembic revision --autogenerate -m "$MESSAGE"
        echo -e "${GREEN}Migration created successfully${NC}"
        ;;
    
    merge|--merge)
        echo -e "${YELLOW}Merging migration branches${NC}"
        run_alembic merge -m "Merge branches"
        echo -e "${GREEN}Branches merged successfully${NC}"
        ;;
    
    help|--help|-h)
        usage
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        usage
        ;;
esac


