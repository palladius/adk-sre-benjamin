#!/bin/bash
set -e

# Load environment variables from .env
if [ -f .env ]; then
  echo "📖 Loading environment variables from .env..."
  # Use grep and sed to clean up export syntax safely
  export $(grep -v '^#' .env | xargs)
else
  echo "⚠️  .env file not found. Falling back to default environment values."
fi

# Set defaults
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: GCP_PROJECT_ID is not configured and no default project is set in gcloud."
  exit 1
fi

REGION=${GCP_REGION:-"us-central1"}
DEFAULT_GEMINI_MODEL=${DEFAULT_GEMINI_MODEL:-"gemini-3.1-flash-lite"}
GCLOUD_IDENTITY=${GCLOUD_IDENTITY:-$(gcloud config get-value account 2>/dev/null)}

# Read VERSION
if [ -f VERSION ]; then
  VERSION=$(cat VERSION | tr -d '\r\n')
else
  VERSION="latest"
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/sre-agent-repo/sre-agent"
echo "🛠️ Target Project: $PROJECT_ID"
echo "🛠️ Target Region:  $REGION"
echo "🛠️ Version tag:     v$VERSION"

# Step 1: Create Artifact Registry repository if it doesn't exist
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create sre-agent-repo \
    --repository-format=docker \
    --location="$REGION" \
    --description="SRE Agent Docker Repository" \
    --project="$PROJECT_ID" || true

# Step 2: Configure Docker authentication
echo "🔑 Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Step 3: Build Docker image locally with dual tags
echo "🐳 Building Docker image locally..."
docker build -t "${IMAGE_BASE}:latest" -t "${IMAGE_BASE}:v${VERSION}" .

# Step 4: Push Docker image to Artifact Registry
echo "🚀 Pushing Docker images..."
docker push "${IMAGE_BASE}:latest"
docker push "${IMAGE_BASE}:v${VERSION}"

# Step 5: Deploy to Cloud Run using the pushed image
echo "🚀 Deploying to Cloud Run with IAP..."
gcloud beta run deploy sre-agent-service \
    --image="${IMAGE_BASE}:latest" \
    --port=8080 \
    --no-allow-unauthenticated \
    --iap \
    --set-env-vars "MOCK_TOOLING=false,SRE_MODE=LIVE,DEFAULT_GEMINI_MODEL=${DEFAULT_GEMINI_MODEL},GCLOUD_IDENTITY=${GCLOUD_IDENTITY}" \
    --region="$REGION" \
    --project="$PROJECT_ID"

echo "✅ Deployment completed successfully!"
