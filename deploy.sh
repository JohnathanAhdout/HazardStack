#!/bin/bash

# SPIRAL Deployment Script
# Usage: ./deploy.sh [web|mobile|api|all] [dev|staging|prod]

set -e

COMPONENT=${1:-all}
ENVIRONMENT=${2:-dev}

echo "🌀 SPIRAL Deployment Script"
echo "Component: $COMPONENT"
echo "Environment: $ENVIRONMENT"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        log_warn "Docker is not installed (optional)"
    fi

    log_info "Prerequisites check passed"
}

# Deploy web app
deploy_web() {
    log_info "Deploying web app..."

    cd web-app

    # Install dependencies
    log_info "Installing dependencies..."
    npm ci

    if [ "$ENVIRONMENT" == "prod" ]; then
        log_info "Building production bundle..."
        npm run build

        # Deploy to Vercel
        if command -v vercel &> /dev/null; then
            log_info "Deploying to Vercel..."
            vercel --prod
        else
            log_warn "Vercel CLI not found. Run: npm i -g vercel"
        fi
    elif [ "$ENVIRONMENT" == "staging" ]; then
        log_info "Building for staging..."
        npm run build
        vercel
    else
        log_info "Starting development server..."
        npm run dev &
    fi

    cd ..
    log_info "Web app deployment complete"
}

# Deploy mobile app
deploy_mobile() {
    log_info "Deploying mobile app..."

    cd mobile-app

    # Install dependencies
    log_info "Installing dependencies..."
    npm ci

    if [ "$ENVIRONMENT" == "prod" ]; then
        # Check for EAS CLI
        if ! command -v eas &> /dev/null; then
            log_error "EAS CLI not found. Run: npm i -g eas-cli"
            exit 1
        fi

        log_info "Building production apps..."
        eas build --platform all --non-interactive

    elif [ "$ENVIRONMENT" == "staging" ]; then
        log_info "Building preview..."
        eas build --platform all --profile preview
    else
        log_info "Starting Expo development server..."
        expo start &
    fi

    cd ..
    log_info "Mobile app deployment complete"
}

# Deploy API
deploy_api() {
    log_info "Deploying API..."

    if [ -f "docker-compose.yml" ]; then
        log_info "Starting services with Docker Compose..."
        docker-compose up -d

        log_info "Waiting for services to be ready..."
        sleep 10

        # Health check
        if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
            log_info "API is healthy"
        else
            log_warn "API health check failed"
        fi
    else
        log_warn "docker-compose.yml not found. Manual deployment required."
    fi

    log_info "API deployment complete"
}

# Deploy all
deploy_all() {
    log_info "Deploying all components..."

    deploy_api
    sleep 5
    deploy_web
    deploy_mobile

    log_info "All components deployed"
}

# Main
main() {
    check_prerequisites

    case $COMPONENT in
        web)
            deploy_web
            ;;
        mobile)
            deploy_mobile
            ;;
        api)
            deploy_api
            ;;
        all)
            deploy_all
            ;;
        *)
            log_error "Unknown component: $COMPONENT"
            echo "Usage: $0 [web|mobile|api|all] [dev|staging|prod]"
            exit 1
            ;;
    esac

    echo ""
    log_info "Deployment complete! 🎉"
    echo ""
    echo "Access your apps:"
    echo "  Web:    http://localhost:3000"
    echo "  API:    http://localhost:8000"
    echo "  Mobile: Scan QR code with Expo Go"
}

main
