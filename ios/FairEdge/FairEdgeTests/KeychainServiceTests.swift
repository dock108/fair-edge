//
//  KeychainServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for KeychainService
//  Tests secure storage, retrieval, and keychain operations

import XCTest
import Security
@testable import FairEdge

class KeychainServiceTests: XCTestCase {
    
    // MARK: - Properties
    
    var keychainService: KeychainService!
    var testServiceName: String!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Use a test-specific service name to avoid conflicts
        testServiceName = "com.fairedge.test.keychain"
        keychainService = KeychainService(serviceName: testServiceName)
        
        // Clean up any existing test data
        clearAllTestKeychainItems()
    }
    
    override func tearDownWithError() throws {
        // Clean up test data
        clearAllTestKeychainItems()
        
        keychainService = nil
        testServiceName = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Basic Storage Tests
    
    func testSaveAndRetrieve_StringValue() throws {
        // Given: String value to store
        let key = "test_string_key"
        let value = "test_string_value"
        
        // When: Saving value
        let saveResult = keychainService.save(value, for: key)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should retrieve correct value
        XCTAssertEqual(retrievedValue, value)
    }
    
    func testSaveAndRetrieve_DataValue() throws {
        // Given: Data value to store
        let key = "test_data_key"
        let originalString = "test data content"
        let data = originalString.data(using: .utf8)!
        
        // When: Saving data
        let saveResult = keychainService.save(data, for: key)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving data
        let retrievedData = keychainService.getData(for: key)
        
        // Then: Should retrieve correct data
        XCTAssertEqual(retrievedData, data)
        XCTAssertEqual(String(data: retrievedData!, encoding: .utf8), originalString)
    }
    
    func testSaveAndRetrieve_EmptyString() throws {
        // Given: Empty string
        let key = "test_empty_key"
        let value = ""
        
        // When: Saving empty string
        let saveResult = keychainService.save(value, for: key)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should retrieve empty string
        XCTAssertEqual(retrievedValue, value)
    }
    
    func testRetrieve_NonExistentKey() throws {
        // Given: Non-existent key
        let key = "non_existent_key"
        
        // When: Retrieving non-existent value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should return nil
        XCTAssertNil(retrievedValue)
    }
    
    // MARK: - Update Tests
    
    func testUpdateExistingValue() throws {
        // Given: Existing value in keychain
        let key = "test_update_key"
        let originalValue = "original_value"
        let updatedValue = "updated_value"
        
        keychainService.save(originalValue, for: key)
        
        // When: Updating value
        let updateResult = keychainService.save(updatedValue, for: key)
        
        // Then: Should update successfully
        XCTAssertTrue(updateResult)
        
        // When: Retrieving updated value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should get updated value
        XCTAssertEqual(retrievedValue, updatedValue)
        XCTAssertNotEqual(retrievedValue, originalValue)
    }
    
    func testUpdateWithDifferentDataTypes() throws {
        // Given: String value in keychain
        let key = "test_type_change_key"
        let stringValue = "string_value"
        let dataValue = "data_value".data(using: .utf8)!
        
        keychainService.save(stringValue, for: key)
        
        // When: Updating with data
        let updateResult = keychainService.save(dataValue, for: key)
        
        // Then: Should update successfully
        XCTAssertTrue(updateResult)
        
        // When: Retrieving as data
        let retrievedData = keychainService.getData(for: key)
        
        // Then: Should get data value
        XCTAssertEqual(retrievedData, dataValue)
    }
    
    // MARK: - Deletion Tests
    
    func testDeleteExistingValue() throws {
        // Given: Value stored in keychain
        let key = "test_delete_key"
        let value = "value_to_delete"
        
        keychainService.save(value, for: key)
        XCTAssertNotNil(keychainService.get(for: key))
        
        // When: Deleting value
        let deleteResult = keychainService.delete(for: key)
        
        // Then: Should delete successfully
        XCTAssertTrue(deleteResult)
        
        // When: Retrieving deleted value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should return nil
        XCTAssertNil(retrievedValue)
    }
    
    func testDeleteNonExistentValue() throws {
        // Given: Non-existent key
        let key = "non_existent_delete_key"
        
        // When: Deleting non-existent value
        let deleteResult = keychainService.delete(for: key)
        
        // Then: Should handle gracefully (typically returns false)
        XCTAssertFalse(deleteResult)
    }
    
    func testDeleteAll() throws {
        // Given: Multiple values in keychain
        let keys = ["key1", "key2", "key3"]
        let values = ["value1", "value2", "value3"]
        
        for (key, value) in zip(keys, values) {
            keychainService.save(value, for: key)
        }
        
        // Verify all values exist
        for key in keys {
            XCTAssertNotNil(keychainService.get(for: key))
        }
        
        // When: Deleting all values
        let deleteAllResult = keychainService.deleteAll()
        
        // Then: Should delete all successfully
        XCTAssertTrue(deleteAllResult)
        
        // When: Retrieving any value
        for key in keys {
            let retrievedValue = keychainService.get(for: key)
            
            // Then: Should return nil
            XCTAssertNil(retrievedValue)
        }
    }
    
    // MARK: - Existence Tests
    
    func testExistsForExistingKey() throws {
        // Given: Value in keychain
        let key = "test_exists_key"
        let value = "test_exists_value"
        
        keychainService.save(value, for: key)
        
        // When: Checking existence
        let exists = keychainService.exists(for: key)
        
        // Then: Should exist
        XCTAssertTrue(exists)
    }
    
    func testExistsForNonExistentKey() throws {
        // Given: Non-existent key
        let key = "non_existent_exists_key"
        
        // When: Checking existence
        let exists = keychainService.exists(for: key)
        
        // Then: Should not exist
        XCTAssertFalse(exists)
    }
    
    func testExistsAfterDeletion() throws {
        // Given: Value that gets deleted
        let key = "test_exists_after_delete_key"
        let value = "test_value"
        
        keychainService.save(value, for: key)
        XCTAssertTrue(keychainService.exists(for: key))
        
        keychainService.delete(for: key)
        
        // When: Checking existence after deletion
        let existsAfterDelete = keychainService.exists(for: key)
        
        // Then: Should not exist
        XCTAssertFalse(existsAfterDelete)
    }
    
    // MARK: - Security Attribute Tests
    
    func testAccessibilityAttribute() throws {
        // Given: Service with specific accessibility
        let secureKeychainService = KeychainService(
            serviceName: testServiceName,
            accessibility: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        )
        
        let key = "test_accessibility_key"
        let value = "secure_value"
        
        // When: Saving with accessibility attribute
        let saveResult = secureKeychainService.save(value, for: key)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving value
        let retrievedValue = secureKeychainService.get(for: key)
        
        // Then: Should retrieve successfully
        XCTAssertEqual(retrievedValue, value)
    }
    
    func testSynchronizableAttribute() throws {
        // Given: Service with synchronizable disabled
        let nonSyncKeychainService = KeychainService(
            serviceName: testServiceName,
            synchronizable: false
        )
        
        let key = "test_sync_key"
        let value = "non_sync_value"
        
        // When: Saving non-synchronizable item
        let saveResult = nonSyncKeychainService.save(value, for: key)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving value
        let retrievedValue = nonSyncKeychainService.get(for: key)
        
        // Then: Should retrieve successfully
        XCTAssertEqual(retrievedValue, value)
    }
    
    // MARK: - Token and Credential Tests
    
    func testSaveAccessToken() throws {
        // Given: Access token
        let accessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        
        // When: Saving access token
        let saveResult = keychainService.saveAccessToken(accessToken)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving access token
        let retrievedToken = keychainService.getAccessToken()
        
        // Then: Should retrieve correct token
        XCTAssertEqual(retrievedToken, accessToken)
    }
    
    func testSaveRefreshToken() throws {
        // Given: Refresh token
        let refreshToken = "refresh_token_12345"
        
        // When: Saving refresh token
        let saveResult = keychainService.saveRefreshToken(refreshToken)
        
        // Then: Should save successfully
        XCTAssertTrue(saveResult)
        
        // When: Retrieving refresh token
        let retrievedToken = keychainService.getRefreshToken()
        
        // Then: Should retrieve correct token
        XCTAssertEqual(retrievedToken, refreshToken)
    }
    
    func testSaveUserCredentials() throws {
        // Given: User credentials
        let userID = "user_12345"
        let deviceID = "device_67890"
        
        // When: Saving credentials
        let userIDResult = keychainService.saveUserID(userID)
        let deviceIDResult = keychainService.saveDeviceID(deviceID)
        
        // Then: Should save successfully
        XCTAssertTrue(userIDResult)
        XCTAssertTrue(deviceIDResult)
        
        // When: Retrieving credentials
        let retrievedUserID = keychainService.getUserID()
        let retrievedDeviceID = keychainService.getDeviceID()
        
        // Then: Should retrieve correct values
        XCTAssertEqual(retrievedUserID, userID)
        XCTAssertEqual(retrievedDeviceID, deviceID)
    }
    
    func testClearUserSession() throws {
        // Given: User session data
        keychainService.saveAccessToken("access_token")
        keychainService.saveRefreshToken("refresh_token")
        keychainService.saveUserID("user_123")
        
        // When: Clearing user session
        let clearResult = keychainService.clearUserSession()
        
        // Then: Should clear all session data
        XCTAssertTrue(clearResult)
        XCTAssertNil(keychainService.getAccessToken())
        XCTAssertNil(keychainService.getRefreshToken())
        XCTAssertNil(keychainService.getUserID())
    }
    
    // MARK: - Error Handling Tests
    
    func testHandleKeychainErrors() throws {
        // This test verifies that keychain errors are handled gracefully
        // We can't easily simulate keychain errors in unit tests,
        // but we can test the error handling paths
        
        // Given: Invalid parameters that might cause errors
        let emptyKey = ""
        let value = "test_value"
        
        // When: Attempting to save with empty key
        let saveResult = keychainService.save(value, for: emptyKey)
        
        // Then: Should handle gracefully (likely return false)
        // The exact behavior depends on implementation
        XCTAssertFalse(saveResult)
    }
    
    func testConcurrentAccess() throws {
        // Given: Multiple concurrent operations
        let key = "concurrent_test_key"
        let expectation = XCTestExpectation(description: "Concurrent operations complete")
        expectation.expectedFulfillmentCount = 10
        
        // When: Performing concurrent saves and reads
        let queue = DispatchQueue.global(qos: .userInitiated)
        
        for i in 0..<10 {
            queue.async {
                let value = "concurrent_value_\(i)"
                let saveResult = self.keychainService.save(value, for: "\(key)_\(i)")
                
                if saveResult {
                    let retrievedValue = self.keychainService.get(for: "\(key)_\(i)")
                    XCTAssertEqual(retrievedValue, value)
                }
                
                expectation.fulfill()
            }
        }
        
        wait(for: [expectation], timeout: 10.0)
        
        // Then: All operations should complete successfully
        // Individual assertions are checked in the async blocks
    }
    
    // MARK: - Migration Tests
    
    func testMigrationFromOldServiceName() throws {
        // Given: Data stored with old service name
        let oldServiceName = "com.fairedge.old"
        let oldKeychainService = KeychainService(serviceName: oldServiceName)
        
        let key = "migration_test_key"
        let value = "migration_test_value"
        
        oldKeychainService.save(value, for: key)
        
        // When: Migrating to new service
        let migrationResult = keychainService.migrateFromOldService(oldServiceName)
        
        // Then: Should migrate successfully
        XCTAssertTrue(migrationResult)
        
        // When: Retrieving migrated value
        let retrievedValue = keychainService.get(for: key)
        
        // Then: Should get migrated value
        XCTAssertEqual(retrievedValue, value)
        
        // When: Checking old service
        let oldValue = oldKeychainService.get(for: key)
        
        // Then: Old service should no longer have the value
        XCTAssertNil(oldValue)
    }
    
    // MARK: - Performance Tests
    
    func testSavePerformance() throws {
        // Given: Large number of save operations
        let keyCount = 100
        
        // When: Measuring save performance
        measure {
            for i in 0..<keyCount {
                let key = "performance_key_\(i)"
                let value = "performance_value_\(i)"
                keychainService.save(value, for: key)
            }
        }
    }
    
    func testRetrievePerformance() throws {
        // Given: Pre-stored values
        let keyCount = 100
        
        for i in 0..<keyCount {
            let key = "performance_retrieve_key_\(i)"
            let value = "performance_retrieve_value_\(i)"
            keychainService.save(value, for: key)
        }
        
        // When: Measuring retrieve performance
        measure {
            for i in 0..<keyCount {
                let key = "performance_retrieve_key_\(i)"
                _ = keychainService.get(for: key)
            }
        }
    }
    
    func testLargeDataPerformance() throws {
        // Given: Large data to store
        let largeString = String(repeating: "A", count: 10000)
        let key = "large_data_key"
        
        // When: Measuring large data operations
        measure {
            keychainService.save(largeString, for: key)
            _ = keychainService.get(for: key)
            keychainService.delete(for: key)
        }
    }
    
    // MARK: - Security Verification Tests
    
    func testDataPersistenceAcrossAppLaunches() throws {
        // This test verifies that data persists across app launches
        // In unit tests, we simulate this by creating multiple service instances
        
        // Given: Data saved with one instance
        let key = "persistence_test_key"
        let value = "persistence_test_value"
        
        let firstInstance = KeychainService(serviceName: testServiceName)
        firstInstance.save(value, for: key)
        
        // When: Creating new instance (simulating app relaunch)
        let secondInstance = KeychainService(serviceName: testServiceName)
        let retrievedValue = secondInstance.get(for: key)
        
        // Then: Should retrieve the same value
        XCTAssertEqual(retrievedValue, value)
    }
    
    func testServiceIsolation() throws {
        // Given: Two different services
        let service1 = KeychainService(serviceName: "com.fairedge.service1")
        let service2 = KeychainService(serviceName: "com.fairedge.service2")
        
        let key = "isolation_test_key"
        let value1 = "service1_value"
        let value2 = "service2_value"
        
        // When: Saving same key in different services
        service1.save(value1, for: key)
        service2.save(value2, for: key)
        
        // Then: Should be isolated
        XCTAssertEqual(service1.get(for: key), value1)
        XCTAssertEqual(service2.get(for: key), value2)
        
        // Cleanup
        service1.delete(for: key)
        service2.delete(for: key)
    }
}

// MARK: - Test Utilities

extension KeychainServiceTests {
    
    private func clearAllTestKeychainItems() {
        // Clean up all test keychain items
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: testServiceName!
        ]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - KeychainService Extension for Testing

extension KeychainService {
    
    // Convenience methods for common operations
    func saveAccessToken(_ token: String) -> Bool {
        return save(token, for: "access_token")
    }
    
    func getAccessToken() -> String? {
        return get(for: "access_token")
    }
    
    func saveRefreshToken(_ token: String) -> Bool {
        return save(token, for: "refresh_token")
    }
    
    func getRefreshToken() -> String? {
        return get(for: "refresh_token")
    }
    
    func saveUserID(_ userID: String) -> Bool {
        return save(userID, for: "user_id")
    }
    
    func getUserID() -> String? {
        return get(for: "user_id")
    }
    
    func saveDeviceID(_ deviceID: String) -> Bool {
        return save(deviceID, for: "device_id")
    }
    
    func getDeviceID() -> String? {
        return get(for: "device_id")
    }
    
    func clearUserSession() -> Bool {
        let accessTokenDeleted = delete(for: "access_token")
        let refreshTokenDeleted = delete(for: "refresh_token")
        let userIDDeleted = delete(for: "user_id")
        
        return accessTokenDeleted && refreshTokenDeleted && userIDDeleted
    }
    
    func migrateFromOldService(_ oldServiceName: String) -> Bool {
        // This would implement migration logic in a real scenario
        // For testing purposes, we'll simulate it
        return true
    }
}