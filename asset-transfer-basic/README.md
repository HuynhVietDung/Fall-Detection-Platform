### Giới thiệu
Hệ thống mạng thử nghiệm test-network được xây dựng với mục tiêu tìm hiểu và\
làm quen với Fabric chứ không phải là mô hình triển khai thực tế.
Trong hệ thống mạng này gồm:
-2 peer org và một peer orderer.
-Để đơn giản hoá, chỉ một nút orderer Raft được sử dụng.
-Để tránh phức tạp, TLS Certificate Authority (CA) không được triển khai. Mọi certificate đều được ban hành bởi root CA.
-Hệ thống mạng mẫu triển khai Fabric với Docker Compose.
Vì các node hoạt động độc lập với nhau trong hệ thống mạng Docker Compose,
test-network không được cấu hình để kết nối tới các node Fabric đang hoạt động khác.
-Đoạn mã lệnh trong ‘test-network/network.sh’ nhằm xây dựng một hệ thống mạng thử nghiệm test-network đơn giản của Fabric.
Hệ thống mạng này bao gồm hai peer, mỗi peer một Org, và một node Raft dịch vụ sắp xếp (Ordering Service node – Orderer).
Ta cũng có thể sử dụng ‘./network.sh’ để tạo kênh và triển khai chuỗi mã chaincode

### Nội dung:

Ở đây Asset đại diện cho dữ liệu thực tế mà ta muốn lưu trữ (Message).
Còn dữ liệu trong block là dữ liệu về các giao dịch đối với các Asset (bao gồm tạo mới (Create), và xóa (Delete)).

Làm việc chủ yếu với 2 thư mục asset-transfer-basic/application-gateway và test-network

Trong thư mục asset-transfer-basic:

- Thư mục chaincode-go define chaincode (smart contract) và các file test.

### Chi tiết hơn về cấu trúc Hyperledge Fabric:

https://drive.google.com/drive/u/0/folders/1XdVlmmc3-OnjC98U3DR2wu3mo8H_6BiC

### Running Code

1. Tạo thư mục làm việc

- mkdir -p $HOME/go/src/github.com/<your_github_userid>
- cd $HOME/go/src/github.com/<your_github_userid>

****Bổ sung: Cần phải cài đặt Golang trước.**** 

2. Tải file cài đặt fabric

- curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh && chmod +x install-fabric.sh

3. Tải fabric docker container

- ./install-fabric.sh docker binary -s

4. Khởi tạo hệ thống mạng test và kênh "mychannel" gồm có 2 peer và 1 orderer

- cd test-network
- ./network.sh up createChannel -c mychannel -ca

5. Deploy chaincode

- ./network.sh deployCC -ccn basic -ccp ../asset-transfer-basic/chaincode-go/ -ccl go

6. Chạy client application với peer0 từ org1

- cd asset-transfer-basic/application-gateway-go
- go run .

7. Cài đặt để có thể chạy CLI từ các Org (trường hợp này là Org2)
- cd test-network
- export PATH=${PWD}/../bin:$PATH
- export FABRIC_CFG_PATH=$PWD/../config/
- export $(./setOrgEnv.sh Org2 | xargs)

- export CORE_PEER_TLS_ENABLED=true
- export CORE_PEER_LOCALMSPID="Org1MSP"
- export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
- export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
- export CORE_PEER_ADDRESS=localhost:7051

8. Sau khi cài đặt thì có thể chạy các lệnh sau dưới quyền của Org1

// Truy vấn toàn bộ asset
- peer chaincode query -C mychannel -n basic -c '{"Args":["GetAllAssets"]}'

// Tạo 1 asset mới
- peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" -C mychannel -n basic --peerAddresses localhost:7051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" --peerAddresses localhost:9051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" -c '{"function":"TransferAsset","Args":["asset6","Christopher"]}'

// Truy vấn 1 asset cụ thể
- peer chaincode query -C mychannel -n basic -c '{"Args":["ReadAsset","asset6"]}'

// Lấy thông tin về blockchain
- peer channel getinfo -c mychannel

// Tải một block cụ thể (block số 25) 
- docker run -it -p 7059:7059 hyperledger/fabric-tools:latest configtxlator start &
- peer channel fetch 25 block_25.pb -o localhost:7050 -c mychannel --tls --cafile $ORDERER_CA

// Decode block tải về
- curl -X POST --data-binary @block_25.pb http://127.0.0.1:7059/protolator/decode/common.Block > block_25.json
