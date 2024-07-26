# Fall-Detection-Platform

### Running Code

1. Make Working Directory:

```
mkdir -p $HOME/go/src/github.com/<your_github_userid>
cd $HOME/go/src/github.com/<your_github_userid>
```

\***\*You need to install Golang first.\*\***

2. Download Fabric Installer

```
curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh
```

3. Install Fabric:

```
./install-fabric.sh docker binary -s
```

4. Initialize test network (2 peers, 1 orderer, 3 ca): \***\*You need to open Docker first.\*\***

```
cd test-network
./network.sh up createChannel -c mychannel -ca
```

5. Deploy chaincode:

```
./network.sh deployCC -ccn basic -ccp ../asset-transfer-basic/chaincode-go/ -ccl go
```

6. Run systems (with 2 camera):

```
cd ./../
chmod +x ci.sh
./ci.sh
```

7. Configuration for running CLI from Org (Chạy cửa sổ terminal mới):

Org 1

```
cd test-network
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export $(./setOrgEnv.sh Org1 | xargs)

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

export CORE_PEER_ADDRESS=localhost:7051
```

Org2

```
cd test-network
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export $(./setOrgEnv.sh Org2 | xargs)

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp

export CORE_PEER_ADDRESS=localhost:9051
```

8. CLI Commands:

Query all Assets

```
peer chaincode query -C mychannel -n basic -c '{"Args":["GetAllAssets"]}'
```

Create New Asset

```
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" -C mychannel -n basic --peerAddresses localhost:7051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" --peerAddresses localhost:9051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" -c '{"function":"TransferAsset","Args":["asset6","QmZkFFDTwCSy7gVhvrX3YoD4FMb2YMZoEq4CeBsPtRL821 - 1 - 1"]}'
```

Query specific Asset

```
peer chaincode query -C mychannel -n basic -c '{"Args":["ReadAsset","asset6"]}'
```

Get blockchain info

```
peer channel getinfo -c mychannel
```

Download a block (eg: block 25)

```
docker run -it -p 7059:7059 hyperledger/fabric-tools:latest configtxlator start &
peer channel fetch 25 block_25.pb -o localhost:7050 -c mychannel --tls --cafile $ORDERER_CA
```

Decode downloaded block

```
curl -X POST --data-binary @block_25.pb http://127.0.0.1:7059/protolator/decode/common.Block > block_25.json
```
