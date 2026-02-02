# bikeshed-image
A bikeshed image to build PlantUML diagrams and the spec at once.

## Usage
```bash
docker build -t bikeshed-image .

# Defaults to spec.bs and outputs to dist/
docker run --rm -v "$PWD":/work bikeshed-image

# Or specify input file and output directory
docker run --rm -v "$PWD":/work bikeshed-image test.bs dist

# Dev mode: watch + live reload server (serves dist/ on port 59754)
docker run --rm -v "$PWD":/work -e DEV=1 -p 59754:59754 bikeshed-image test.bs dist

# Open in browser
# http://localhost:59754/

# Change dev server port
docker run --rm -v "$PWD":/work -e DEV=1 -e PORT=8080 -p 8080:8080 bikeshed-image test.bs dist
```

Outputs:
- `dist/spec.bs` (preprocessed input)
- `dist/index.html` (generated spec)
- `dist/uml/*.svg` (PlantUML diagrams rendered locally in the image)
