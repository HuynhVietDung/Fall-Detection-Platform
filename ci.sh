function print() {
	GREEN='\033[0;32m'
  NC='\033[0m'
  echo
	echo -e "${GREEN}${1}${NC}"
}

# Define paths to your Python and Go scripts
PYTHON_SCRIPT_1="test/record_video_1.py"
PYTHON_SCRIPT_2="test/record_video_2.py"

GO_SCRIPT_1="assetTransfer_dummy.go"
GO_SCRIPT_2="assetTransfer.go"

# Function to run Python and Go scripts in parallel and display output
function run_py_script() {
  print "Running $1"
  python3 $1 | tee "${1%.py}.log"  # Run Python script and save/display output
}

function run_go_script(){
  print "Running $1"
  pushd asset-transfer-basic/application-gateway-go/
  go run $1 | tee "${1%.go}.log" # Run Go script and save/display output
  popd
}

# Enable debug mode
set -x

(trap 'kill 0' SIGINT;  run_py_script $PYTHON_SCRIPT_1 & run_go_script $GO_SCRIPT_1 & run_py_script $PYTHON_SCRIPT_2 & run_go_script $GO_SCRIPT_2 && fg)

# Disable debug mode
{ set +x; } 2>/dev/null
