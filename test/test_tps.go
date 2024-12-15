/*
Copyright 2021 IBM All Rights Reserved.

SPDX-License-Identifier: Apache-2.0
*/

package main

import (
	"bytes"
	"context"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path"
	"time"
	"bufio"
	"math/rand"
	"github.com/hyperledger/fabric-gateway/pkg/client"
	"github.com/hyperledger/fabric-gateway/pkg/identity"
	"github.com/hyperledger/fabric-protos-go-apiv2/gateway"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/status"
	"io/ioutil"
	"log"
)

const (
	mspID        = "Org2MSP"
	cryptoPath   = "../../test-network/organizations/peerOrganizations/org2.example.com"
	certPath     = cryptoPath + "/users/User1@org2.example.com/msp/signcerts"
	keyPath      = cryptoPath + "/users/User1@org2.example.com/msp/keystore"
	tlsCertPath  = cryptoPath + "/peers/peer0.org2.example.com/tls/ca.crt"
	peerEndpoint = "dns:///localhost:9051"
	gatewayPeer  = "peer0.org2.example.com"
)

func main() {
	// The gRPC client connection should be shared by all Gateway connections to this endpoint
	clientConnection := newGrpcConnection()
	defer clientConnection.Close()

	id := newIdentity()
	sign := newSign()

	// Create a Gateway connection for a specific client identity
	gw, err := client.Connect(
		id,
		client.WithSign(sign),
		client.WithClientConnection(clientConnection),
		// Default timeouts for different gRPC calls
		client.WithEvaluateTimeout(5*time.Second),
		client.WithEndorseTimeout(15*time.Second),
		client.WithSubmitTimeout(5*time.Second),
		client.WithCommitStatusTimeout(1*time.Minute),
	)
	if err != nil {
		panic(err)
	}
	defer gw.Close()

	// Override default values for chaincode and channel name as they may differ in testing contexts.
	chaincodeName := "basic"
	if ccname := os.Getenv("CHAINCODE_NAME"); ccname != "" {
		chaincodeName = ccname
	}

	channelName := "mychannel"
	if cname := os.Getenv("CHANNEL_NAME"); cname != "" {
		channelName = cname
	}

	network := gw.GetNetwork(channelName)
	contract := network.GetContract(chaincodeName)
	
	filepath := "/Users/huynhvietdung/go/src/github.com/HuynhVietDung/FallDetectionBlockChain/Fall-Detection-Platform/fall.txt"
	readFileTxtAndCreateAsset(contract, filepath)
	//process(contract)
}


// newGrpcConnection creates a gRPC connection to the Gateway server.
func newGrpcConnection() *grpc.ClientConn {
	certificatePEM, err := os.ReadFile(tlsCertPath)
	if err != nil {
		panic(fmt.Errorf("failed to read TLS certifcate file: %w", err))
	}

	certificate, err := identity.CertificateFromPEM(certificatePEM)
	if err != nil {
		panic(err)
	}

	certPool := x509.NewCertPool()
	certPool.AddCert(certificate)
	transportCredentials := credentials.NewClientTLSFromCert(certPool, gatewayPeer)

	connection, err := grpc.NewClient(peerEndpoint, grpc.WithTransportCredentials(transportCredentials))
	if err != nil {
		panic(fmt.Errorf("failed to create gRPC connection: %w", err))
	}

	return connection
}

// newIdentity creates a client identity for this Gateway connection using an X.509 certificate.
func newIdentity() *identity.X509Identity {
	certificatePEM, err := readFirstFile(certPath)
	if err != nil {
		panic(fmt.Errorf("failed to read certificate file: %w", err))
	}

	certificate, err := identity.CertificateFromPEM(certificatePEM)
	if err != nil {
		panic(err)
	}

	id, err := identity.NewX509Identity(mspID, certificate)
	if err != nil {
		panic(err)
	}

	return id
}

// newSign creates a function that generates a digital signature from a message digest using a private key.
func newSign() identity.Sign {
	privateKeyPEM, err := readFirstFile(keyPath)
	if err != nil {
		panic(fmt.Errorf("failed to read private key file: %w", err))
	}

	privateKey, err := identity.PrivateKeyFromPEM(privateKeyPEM)
	if err != nil {
		panic(err)
	}

	sign, err := identity.NewPrivateKeySign(privateKey)
	if err != nil {
		panic(err)
	}

	return sign
}

func readFirstFile(dirPath string) ([]byte, error) {
	dir, err := os.Open(dirPath)
	if err != nil {
		return nil, err
	}

	fileNames, err := dir.Readdirnames(1)
	if err != nil {
		return nil, err
	}

	return os.ReadFile(path.Join(dirPath, fileNames[0]))
}

// This type of transaction would typically only be run once by an application the first time it was started after its
// initial deployment. A new version of the chaincode deployed later would likely not need to run an "init" function.
func initLedger(contract *client.Contract) {
	fmt.Printf("\n--> Submit Transaction: InitLedger, function creates the initial set of assets on the ledger \n")

	_, err := contract.SubmitTransaction("InitLedger")
	if err != nil {
		//panic(fmt.Errorf("failed to submit transaction: %w", err))
		ErrorHandling(err)
	}

	fmt.Printf("*** Transaction committed successfully\n")
}

// Evaluate a transaction to query ledger state.
func getAllAssets(contract *client.Contract) {
	fmt.Println("\n--> Evaluate Transaction: GetAllAssets, function returns all the current assets on the ledger")

	evaluateResult, err := contract.EvaluateTransaction("GetAllAssets")
	if err != nil {
		panic(fmt.Errorf("failed to evaluate transaction: %w", err))
	}
	result := formatJSON(evaluateResult)

	fmt.Printf("*** Result:%s\n", result)
}

// Submit a transaction synchronously, blocking until it has been committed to the ledger.
func createAsset(contract *client.Contract, message string) {	
	var now = time.Now()
	rand.Seed(now.UnixNano())
	randomNumber := rand.Intn(999999)
	assetID := fmt.Sprintf("asset%d", now.Unix()*1e3+int64(now.Nanosecond())/1e6 + int64(randomNumber))

	// fmt.Printf("\n--> Submit Transaction: CreateAsset, creates new asset with ID: %s\n", assetID)

	_, err := contract.SubmitTransaction("CreateAsset", assetID, message)
	if err != nil {
		//panic(fmt.Errorf("failed to submit transaction: %w", err))
		ErrorHandling(err)
	}

	// fmt.Printf("*** Transaction committed successfully\n")
}

func readFileTxtAndCreateAsset(contract *client.Contract, filePath string) {
	// Open file
	file, err := os.Open(filePath)
	if err != nil {
		panic(fmt.Errorf("failed to open file: %w", err))
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	// Read lines
	currentTime := time.Now()
	for scanner.Scan() {
		message := scanner.Text()
		createAsset(contract, message)
		timeDifference := time.Now().Sub(currentTime)
		timeDifferenceInSeconds := timeDifference.Seconds()

		fmt.Printf("Second %.0fth", timeDifferenceInSeconds)
		// Chuyển chênh lệch thời gian thành số giây
		if timeDifferenceInSeconds > 60.0 {
			break
		}

	}
            
	if err := scanner.Err(); err != nil {
		panic(fmt.Errorf("Error while reading file: %w", err))
	}
}

func readFileTxtAndCreateAsset2(contract *client.Contract, filePath string) {
	for {
		// Open file
		file, err := os.Open(filePath)
		if err != nil {
			panic(fmt.Errorf("failed to open file: %w", err))
		}

		scanner := bufio.NewScanner(file)
		lines := []string{}

		// Read first line
		var firstLine string
		if scanner.Scan() {
			firstLine = scanner.Text()
		} else {
			file.Close()
			if err := scanner.Err(); err != nil {
				panic(fmt.Errorf("Error while reading file: %w", err))
			}
			break // Exit loop if no more lines
		}

		// Store remaining lines
		for scanner.Scan() {
			lines = append(lines, scanner.Text())
		}

		if err := scanner.Err(); err != nil {
			file.Close()
			panic(fmt.Errorf("Error while reading file: %w", err))
		}
		file.Close()

		// Process the first line
		createAsset(contract, firstLine)

		// Write remaining lines back to the file
		file, err = os.Create(filePath)
		if err != nil {
			panic(fmt.Errorf("failed to create file: %w", err))
		}

		writer := bufio.NewWriter(file)
		for _, line := range lines {
			_, err := writer.WriteString(line + "\n")
			if err != nil {
				file.Close()
				panic(fmt.Errorf("Error while writing to file: %w", err))
			}
		}

		err = writer.Flush()
		if err != nil {
			file.Close()
			panic(fmt.Errorf("Error while flushing writer: %w", err))
		}

		file.Close()
	}
}


func process(contract *client.Contract){
	maxAttempts := -1
    attempts := 0


    for attempts > maxAttempts {
        files, err := ioutil.ReadDir("../../result_folder_dummy")
        if err != nil {
            if os.IsNotExist(err) {
                log.Println("Directory 'result_folder_dummy' does not exist. Retrying...")
            } else {
                log.Fatalf("Failed to read directory 'result': %v", err)
            }
            attempts++
            time.Sleep(10 * time.Second) // Wait for 10 seconds before retrying
            continue
        }

        if len(files) == 0 {
            attempts++
            log.Println("No files found. Attempt", attempts)
            time.Sleep(10 * time.Second) // Wait for 10 seconds before retrying
            continue
        }

        attempts = 0 // Reset attempts counter if files are found
		
		currentTime := time.Now()
        for _, file := range files {
            if !file.IsDir() {
				// Tính chênh lệch thời gian
				timeDifference := time.Now().Sub(currentTime)

				// Chuyển chênh lệch thời gian thành số giây
				timeDifferenceInSeconds := timeDifference.Seconds()
				if timeDifferenceInSeconds > 60.0 {
					break
				}
                filePath := "../../result_folder_dummy/" + file.Name()
                readFileTxtAndCreateAsset(contract, filePath)
				fmt.Printf("%.0f",timeDifferenceInSeconds)

                err := os.Remove(filePath)
                if err != nil {
                    log.Printf("Failed to remove file %s: %v", filePath, err)
                }
            }
        }
    }
}

// Submit transaction, passing in the wrong number of arguments ,expected to throw an error containing details of any error responses from the smart contract.
func ErrorHandling(err error) {
	fmt.Println("*** Caught the error:")

	var endorseErr *client.EndorseError
	var submitErr *client.SubmitError
	var commitStatusErr *client.CommitStatusError
	var commitErr *client.CommitError

	if errors.As(err, &endorseErr) {
		fmt.Printf("Endorse error for transaction %s with gRPC status %v: %s\n", endorseErr.TransactionID, status.Code(endorseErr), endorseErr)
	} else if errors.As(err, &submitErr) {
		fmt.Printf("Submit error for transaction %s with gRPC status %v: %s\n", submitErr.TransactionID, status.Code(submitErr), submitErr)
	} else if errors.As(err, &commitStatusErr) {
		if errors.Is(err, context.DeadlineExceeded) {
			fmt.Printf("Timeout waiting for transaction %s commit status: %s", commitStatusErr.TransactionID, commitStatusErr)
		} else {
			fmt.Printf("Error obtaining commit status for transaction %s with gRPC status %v: %s\n", commitStatusErr.TransactionID, status.Code(commitStatusErr), commitStatusErr)
		}
	} else if errors.As(err, &commitErr) {
		fmt.Printf("Transaction %s failed to commit with status %d: %s\n", commitErr.TransactionID, int32(commitErr.Code), err)
	} else {
		panic(fmt.Errorf("unexpected error type %T: %w", err, err))
	}

	// Any error that originates from a peer or orderer node external to the gateway will have its details
	// embedded within the gRPC status error. The following code shows how to extract that.
	statusErr := status.Convert(err)

	details := statusErr.Details()
	if len(details) > 0 {
		fmt.Println("Error Details:")

		for _, detail := range details {
			switch detail := detail.(type) {
			case *gateway.ErrorDetail:
				fmt.Printf("- address: %s, mspId: %s, message: %s\n", detail.Address, detail.MspId, detail.Message)
			}
		}
	}
}

// Format JSON data
func formatJSON(data []byte) string {
	var prettyJSON bytes.Buffer
	if err := json.Indent(&prettyJSON, data, "", "  "); err != nil {
		panic(fmt.Errorf("failed to parse JSON: %w", err))
	}
	return prettyJSON.String()
}


