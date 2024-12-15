function print() {
	GREEN='\033[0;32m'
  NC='\033[0m'
  echo
	echo -e "${GREEN}${1}${NC}"
}

# Define paths to your Python and Go scripts
PYTHON_SCRIPT="src/record_video.py"
GO_SCRIPT="asset-transfer-basic/application-gateway-go/assetTransfer.go"

# Define arguments
## Define arguments for first process
video_path_1="output_1"
txt_path_1="result_1"
camera_idx_1=0
mspID_1="Org1MSP"
cryptoPath_1="../../test-network/organizations/peerOrganizations/org1.example.com"
certPath_1="/users/User1@org1.example.com/msp/signcerts"
keyPath_1="/users/User1@org1.example.com/msp/keystore"
tlsCertPath_1="/peers/peer0.org1.example.com/tls/ca.crt"
peerEndpoint_1="dns:///localhost:7051"
gatewayPeer_1="peer0.org1.example.com"

## Define arguments for second process
video_path_1="output_2"
video_path_2="output_2"
txt_path_2="result_2"
camera_idx_2=1
mspID_2="Org2MSP"
cryptoPath_2="../../test-network/organizations/peerOrganizations/org2.example.com"    
certPath_2="/users/User1@org2.example.com/msp/signcerts"
keyPath_2="/users/User1@org2.example.com/msp/keystore" 
tlsCertPath_2="/peers/peer0.org2.example.com/tls/ca.crt"
peerEndpoint_2="dns:///localhost:9051"
gatewayPeer_2="peer0.org2.example.com"

# Function to run Python and Go scripts in parallel and display output
function run_fall_detection_system() {
  print "Running $1"
  python3 $1 $2 $3 $4 | tee "${1%.py}.log"  # Run Python script and save/display output
}

function run_blockchaint_network(){
  print "Running $1"
  go run $1 \
  -mspID $2 \
  -cryptoPath $3 \
  -certPath $4 \
  -keyPath $5 \
  -tlsCertPath $6 \
  -peerEndpoint $7 \
  -gatewayPeer $8 | tee "${1%.go}.log" # Run Go script and save/display output
  popd
}

# Enable debug mode
set -x

(trap 'kill 0' SIGINT; \
run_fall_detection_system $PYTHON_SCRIPT $video_path_1 $txt_path_1 $camera_idx_1 & \
run_blockchaint_network $GO_SCRIPT_1 $mspID_1 $cryptoPath_1 $certPath_1 $keyPath_1 $tlsCertPath_1 $peerEndpoint_1 $gatewayPeer_1  & \
run_fall_detection_system $PYTHON_SCRIPT $video_path_2 $txt_path_2 $camera_idx_2  & \
run_blockchaint_network $GO_SCRIPT_2 $mspID_2 $cryptoPath_2 $certPath_2 $keyPath_2 $tlsCertPath_2 $peerEndpoint_2 $gatewayPeer_2 && \
fg)

# Disable debug mode
{ set +x; } 2>/dev/null
